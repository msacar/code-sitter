const users = [
  { id: 1, name: "John" },
  { id: 2, name: "Jane" },
  { id: 3, name: "Bob" }
];

function sayHello(id: number) {
  const user = getUser(id);
  console.log(user?.name.toLowerCase());
  return user?.name.toString();
}

function getUser(id: number) {
  return users.find(u => u.id === id);
}

// Test async function with calls
async function loadUserData(userId: number) {
  const user = getUser(userId);
  if (!user) {
    console.error("User not found");
    return null;
  }

  const greeting = sayHello(userId);
  console.log(`Greeting: ${greeting}`);

  // Simulate API call
  const response = await fetch(`/api/users/${userId}`);
  const data = await response.json();

  return data;
}

// Arrow function with calls
const processUsers = () => {
  users.forEach(user => {
    sayHello(user.id);
    console.log(`Processed user ${user.id}`);
  });
};
