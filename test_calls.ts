const users= {
    "1" : {
        name: "John",
    }
}
function sayHello(id:number) {
    const user=  getUser(id)
    const helloText = `Hello ${user.name}`.toLowerCase()
    return helloText.toString()
}

function getUser(id: number){
    return users[id]
}

