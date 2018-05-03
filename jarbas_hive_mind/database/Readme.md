## Hive Database

sql database interaction, track the Hive Mind Clients and API keys

the [Flask Hive Node]() provides a REST api for some database interactions

## Client connections

adding a new api connection

    from jarbas_hive_mind.database.client import ClientDatabase

    db = ClientDatabase(debug=True)
    name = "jarbas"
    mail = "jarbasaai@mailfence.com"
    api = "admin_key"
    db.add_client(name, mail, api, admin=True)
