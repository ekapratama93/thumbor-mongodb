# thumbor-mongodb

MongoDB storage adapter for Thumbor. This is a fork from original Thumbor Community version of [tc_mongodb]("https://github.com/thumbor-community/mongodb). 
Additional feature includes:

1. Support for `MONGO_URI`
2. Support for Result Storage
3. Ensure MongoDB index to speedup query
4. Singleton Connection Pool

## Configuration

### MONGO STORAGE OPTIONS

```bash
MONGO_STORAGE_SERVER_HOST = 'localhost' # MongoDB storage server host
MONGO_STORAGE_SERVER_PORT = 27017 # MongoDB storage server port
MONGO_STORAGE_SERVER_DB = 'thumbor' # MongoDB storage server database name
MONGO_STORAGE_SERVER_COLLECTION = 'images' # MongoDB storage image collection
```

### MONGO RESULT STORAGE OPTIONS

```bash
MONGO_RESULT_STORAGE_SERVER_HOST = 'localhost' # MongoDB storage server host
MONGO_RESULT_STORAGE_SERVER_PORT = 27017 # MongoDB storage server port
MONGO_RESULT_STORAGE_SERVER_DB = 'thumbor' # MongoDB storage server database name
MONGO_RESULT_STORAGE_SERVER_COLLECTION = 'images' # MongoDB storage image collection
```

Or you can use Mongo DB URI to create connection for something like ReplicaSet

### MONGO STORAGE

```bash
MONGO_STORAGE_URI = 'mongodb://localhost:27017'
```

### MONGO RESULT STORAGE

```bash
MONGO_RESULT_STORAGE_URI = 'mongodb://localhost:27017'
```

If both configuration exist, URI config will be prioritized.

## Installation

You can install using Pip by referring to this github repo.

```bash
pip install git+https://github.com/ekapratama93/thumbor-mongodb.git
```

And then you need to set `STORAGE` and/or `RESULT_STORAGE` in your thumbor configuration

```conf
STORAGE = 'thumbor_mongodb.storages.mongo_storage'

RESULT_STORAGE = 'thumbor_mongodb.result_storages.mongo_storage'
```
