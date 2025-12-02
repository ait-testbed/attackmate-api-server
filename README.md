pip install fastapi uvicorn httpx PyYAML pydantic argon2_cffi


uvicorn remote_rest.main:app --host 0.0.0.0 --port 8000 --reload

[] TODO sort out logs for different instances

[] TODO return logs to caller

[] TODO limit max. concurent instance number

[] TODO concurrency for several instances?

[] TODO add authentication

[] TODO queue requests for instances

[] TODO dynamic configuration of attackmate config

[] TODO make logging (debug, json etc) configurable at runtime (endpoint or user query paramaters?)


[x] TODO seperate router modules?



# Certificate generation
preliminary, automate later?
with open ssl
    ```bash
    openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
    ```

Common Name: localhost (or ip adress the server will be)


running client:

```bash
python -m client --cacert <path_to_cert> login user user
```
