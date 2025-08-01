// Test file for enhanced structure extraction

export class ComplexClass {
    private privateField: string = "private";
    protected protectedField: number = 42;
    public publicField: boolean = true;

    constructor(name: string) {
        this.privateField = name;
    }

    public async publicMethod(id: number): Promise<string> {
        return `Public method ${id}`;
    }

    private privateMethod(): void {
        console.log("Private method");
    }

    protected protectedMethod(data: any): boolean {
        return !!data;
    }

    static staticMethod(): string {
        return "Static method";
    }

    public static async staticAsyncMethod(count: number): Promise<number[]> {
        return Array(count).fill(0);
    }
}

export interface ComplexInterface {
    id: number;
    name: string;
    nested: {
        value: string;
        optional?: boolean;
    };
}

export type ComplexType = {
    variant: 'A' | 'B' | 'C';
    data: ComplexInterface;
};
