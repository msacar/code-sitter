import { Request, Response } from 'express';
import * as fs from 'fs';
import axios from 'axios';

interface User {
  id: string;
  name: string;
  email: string;
}

export async function getUser(req: Request, res: Response): Promise<void> {
  const userId = req.params.id;

  try {
    const response = await axios.get(`https://api.example.com/users/${userId}`);
    const user: User = response.data;

    // Log the request
    console.log(`Fetched user: ${user.name}`);

    res.json(user);
  } catch (error) {
    console.error('Error fetching user:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
}

export function processData(data: string[]): string[] {
  return data.map(item => item.trim().toLowerCase());
}
