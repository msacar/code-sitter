// Test nested structures for qualified names

export namespace UserManagement {
    export interface IUser {
        id: number;
        name: string;
    }

    export class UserService {
        private users: Map<number, IUser> = new Map();

        public async getUser(id: number): Promise<IUser | null> {
            return this.users.get(id) || null;
        }

        public addUser(user: IUser): void {
            this.users.set(user.id, user);
        }

        static createDefaultUser(): IUser {
            return { id: 0, name: "Default" };
        }
    }

    export enum UserRole {
        Admin = "ADMIN",
        User = "USER",
        Guest = "GUEST"
    }
}

// Test deeply nested function
export const utils = {
    validators: {
        isValidEmail: (email: string): boolean => {
            return email.includes('@');
        },
        isValidPhone: (phone: string): boolean => {
            return phone.length >= 10;
        }
    }
};
