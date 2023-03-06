db = db.getSiblingDB('calendar')

db.createCollection('calendar')

db.createCollection('telegrams', {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: [ "full_name", "user_id" ],
            properties: {
                full_name: {
                    bsonType: "string",
                    description: "Полное имя владельца данного Telegram ID"
                },
                user_id: {
                     bsonType: "int",
                    description: "Telegram ID пользователя"
                }
            }
        }
    }
})