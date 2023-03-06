db = db.getSiblingDB('calendar')

db.createCollection('calendar', {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: [ "owner", "day", "month", "weekday", "hours" ],
            properties: {
                owner: {
                    bsonType: "string",
                    description: "ФИО владельца календаря"
                },
                day: {
                    bsonType: "int",
                    description: "День месяца (число)"
                },
                month: {
                    bsonType: "int",
                    description: "Номер месяца"
                },
                weekday: {
                    bsonType: "int",
                    description: "Номер дня недели"
                },
                hours: {
                    bsonType: "double",
                    description: "Количество отработанных часов в данный день"
                }
            }
        }
    }
})

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