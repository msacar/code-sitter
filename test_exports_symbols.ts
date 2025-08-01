// Test file to demonstrate exports and symbols extraction

// Regular exports
export const API_VERSION = "1.0.0";
export let currentUser: User | null = null;

// Named exports with types
export interface User {
    id: number;
    name: string;
    email: string;
}

export type UserRole = "admin" | "user" | "guest";

// Default export
export default class UserService {
    private users: Map<number, User> = new Map();

    constructor() {
        console.log("UserService initialized");
    }

    async getUser(id: number): Promise<User | null> {
        return this.users.get(id) || null;
    }

    addUser(user: User): void {
        this.users.set(user.id, user);
    }
}

// Export with destructuring
export { UserService as Service };

// Re-export from another module
export { validateEmail } from "./utils";

// Export all from module
export * from "./constants";

// Non-exported symbols (private to module)
const INTERNAL_VERSION = "1.0.0-internal";

function internalHelper(data: any): boolean {
    return true;
}

class InternalCache {
    private cache = new Map();
}

// Complex export patterns
export const userFactory = {
    createUser: (name: string): User => ({
        id: Date.now(),
        name,
        email: `${name}@example.com`
    }),

    createAdmin: (name: string): User => ({
        id: Date.now(),
        name,
        email: `admin.${name}@example.com`
    })
};

// Export enum
export enum UserStatus {
    Active = "ACTIVE",
    Inactive = "INACTIVE",
    Pending = "PENDING"
}

// Export namespace
export namespace UserUtils {
    export function isValidUser(user: any): user is User {
        return user && typeof user.id === "number" && typeof user.name === "string";
    }

    export const MAX_USERS = 1000;
}
