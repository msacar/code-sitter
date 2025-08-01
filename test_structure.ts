// Test file for structure extraction
import { useState, useEffect } from 'react';
import type { User } from './types';

interface User {
    id: number;
    name: string;
    email?: string;
}

type UserRole = 'admin' | 'user' | 'guest';

enum Status {
    Active = 1,
    Inactive = 0
}

export async function getUser(id: number): Promise<User | null> {
    const response = await fetch(`/api/users/${id}`);
    return response.json();
}

export const validateUser = (user: User): boolean => {
    return user.name.length > 0;
};

class UserService {
    private users: User[] = [];

    constructor(private db: Database) {}

    async addUser(user: User): Promise<void> {
        this.users.push(user);
        await this.db.save(user);
    }

    findUser(id: number): User | undefined {
        return this.users.find(u => u.id === id);
    }
}

// Generic function example
function map<T, U>(items: T[], fn: (item: T) => U): U[] {
    return items.map(fn);
}
