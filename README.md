# thumbor-mongodb

MongoDB storage adapter for Thumbor.

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
