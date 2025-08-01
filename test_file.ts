import { DynamicLinkInstance, DynamicLinkData } from '@shortlink/types'
import { CreateDynamicLinkInstanceRequest, UpdateDynamicLinkInstanceRequest } from '@shortlink/types/request'
import { LinkCodeGenerator } from '../utils/link-code-generator'
import { S3Storage } from '../utils/s3-storage'

const bucketName = process.env.LINKS_BUCKET_NAME || 'shortlinkstack-links-storage'
const storage = new S3Storage(bucketName, process.env.AWS_REGION)
const codeGenerator = new LinkCodeGenerator()

export async function createInstance(
    tenantId: string,
    apiKey: string,
    userAgent: string,
    body: CreateDynamicLinkInstanceRequest & { linkCode: string },
): Promise<{ instance: DynamicLinkInstance }> {
    const { linkCode, ...instanceData } = body

    // Validate template exists
    const template = await storage.getDynamicLink(tenantId, linkCode)
    if (!template) {
        throw new Error('Template not found')
    }

    // Validate all required variables are provided
    for (const variable of template.variables) {
        if (!instanceData.variables[variable]) {
            throw new Error(`Missing required variable: ${variable}`)
        }
    }

    // Generate dynamic code (4 characters)
    let dynamicCode: string
    let attempts = 0
    const maxAttempts = 10

    // Generate unique dynamic code (4 characters)
    do {
        dynamicCode = codeGenerator.generateCode(4) // Generate 4-character code
        attempts++
        // Check if instance exists for this template
        const existing = await storage.getDynamicInstance(tenantId, linkCode, dynamicCode)
        if (!existing) break
    } while (attempts < maxAttempts)

    if (attempts >= maxAttempts) {
        throw new Error('Failed to generate unique dynamic code')
    }

    // Store instance with flattened structure
    const instance: DynamicLinkInstance = {
        ...instanceData,
        linkCode,
        dynamicCode,
        link: instanceData.link || template.link, // Fallback to template link
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        metadata: {
            apiKey: `${apiKey.substring(0, 8)}...`,
            createdBy: 'api',
            userAgent: userAgent || 'unknown',
        },
    }

    await storage.putDynamicInstance(tenantId, linkCode, dynamicCode, instance)
    return { instance }
}

export async function deleteInstance(tenantId: string, linkCode: string, dynamicCode: string): Promise<void> {
    // Check if template exists
    const template = await storage.getDynamicLink(tenantId, linkCode)
    if (!template) {
        throw new Error('Template not found')
    }

    // Check if instance exists
    const instance = await storage.getDynamicInstance(tenantId, linkCode, dynamicCode)
    if (!instance) {
        throw new Error('Instance not found')
    }

    // Delete the instance
    await storage.deleteDynamicInstance(tenantId, linkCode, dynamicCode)
}

export async function getInstance(tenantId: string, linkCode: string, dynamicCode: string): Promise<DynamicLinkInstance | null> {
    // Check if template exists
    const template = await storage.getDynamicLink(tenantId, linkCode)
    if (!template) {
        throw new Error('Template not found')
    }

    // Get the specific instance
    const instance = await storage.getDynamicInstance(tenantId, linkCode, dynamicCode)
    return instance
}

export async function listInstances(tenantId: string, linkCode: string): Promise<{ instances: DynamicLinkInstance[]; template: any }> {
    // Check if template exists
    const template = await storage.getDynamicLink(tenantId, linkCode)
    if (!template) {
        throw new Error('Template not found')
    }

    // List all instances
    const instances = await storage.listDynamicLinkInstances(tenantId, linkCode)

    return { instances, template }
}

export async function updateInstance(
    tenantId: string,
    linkCode: string,
    dynamicCode: string,
    updates: UpdateDynamicLinkInstanceRequest,
): Promise<DynamicLinkInstance> {
    // Check if template exists
    const template = await storage.getDynamicLink(tenantId, linkCode)
    if (!template) {
        throw new Error('Template not found')
    }

    // If variables are being updated, validate them
    if (updates.variables) {
        for (const variable of template.variables) {
            if (!updates.variables[variable]) {
                throw new Error(`Missing required variable: ${variable}`)
            }
        }
    }

    const updatedInstance = await storage.updateDynamicInstance(tenantId, linkCode, dynamicCode, updates)

    if (!updatedInstance) {
        throw new Error('Instance not found')
    }

    return updatedInstance
}
