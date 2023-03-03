# UntitledQL

> ⚠ Note\
> The project has been discontinued due to limitations in the developer experience when using Django with this project. While Django is a powerful framework, it may not have provided the level of convenience and flexibility needed for this particular project. As a result, I plan to rewrite the project using a more bare framework to better meet the project's requirements and improve the overall developer experience

UntitledQL is a rest implementation with stolen features from graphql. While this doesnt resemble graphql by any means, UQL might offer some features simliar to gql;

## Feature

- Call all your api services from one endpoint
- Query your models from client without explicit implementation from your side. CRUD functions are provided out of the box
- Select specific fields from api response
- Subscribe to events without the use of web sockets [would require client implementation : `in-development`]
- Easily setup permissions for model operations

## Docs

> 🛈 Refrences to api calls are written in Curl

- [Setup](docs/setup.md)
- [Functions](docs/functions.md)
