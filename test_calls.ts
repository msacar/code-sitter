// Test file for debugging analyze command
import { useState } from 'react';
import { Logger } from './logger';

interface User {
  id: number;
  name: string;
}

export class UserService {
  private logger: Logger;

  constructor() {
    this.logger = new Logger('UserService');
  }

  async getUser(id: number): Promise<User> {
    this.logger.log(`Fetching user ${id}`);
    const response = await fetch(`/api/users/${id}`);
    return response.json();
  }

  updateUser(user: User): void {
    console.log('Updating user:', user);
    this.logger.debug('User update', user);
  }
}

export const createUserService = () => {
  return new UserService();
};

// Test function calls
function testCalls() {
  const service = createUserService();
  service.getUser(123);
  service.updateUser({ id: 123, name: 'Test' });

  // React hooks
  const [count, setCount] = useState(0);
  setCount(count + 1);
}
