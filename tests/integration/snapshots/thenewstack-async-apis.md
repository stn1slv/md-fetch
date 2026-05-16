# API Management for Asynchronous APIs

The right API management solution should combine traditional API management capabilities with an event-driven architecture.

WSO2 sponsored this post.

[![](https://cdn.thenewstack.io/media/2021/03/8cc7ce46-1597916168571.jpeg)

Menaka Jayawardena

Menaka is an Associate Technical Lead at WSO2, focusing on the research and development of the WSO2 API Microgateway product.](https://www.linkedin.com/in/menakajayawardena/)

Today, customers increasingly demand access to real-time information like stock prices, train times, etc. Delivering this critical information, as it occurs, is a challenging task for every business. Traditionally, applications polled backend servers to fetch the latest information; however, this proved to be inefficient, as it consumes a significant amount of resources.

APIs should be designed to allow users to receive a stream of events from the service, instead of polling it periodically. Event-driven APIs or asynchronous (async) APIs can be used to meet this requirement — with mission-critical information pushed to client applications at the time of the event.

## What Are Async APIs and How Are They Different from REST APIs?

Unlike conventional request/response APIs (e.g., REST and SOAP), asynchronous APIs can send multiple responses to a single request. This can also be in the form of unidirectional or bi-directional communication. There are several protocols that can be used for async APIs, such as Websockets, WebHooks, MQTT, and Server-Sent Events (SSE). Most of these protocols support HTTP at the connection creation stage and use a specific channel to transfer the subsequent messages between the client and the server. Also, conventional HTTP verbs (i.e., GET, POST, PUT, etc.) are not valid for these channels.

Another prominent difference between a REST API and an async API is the usage of an event backbone technology (a message broker such as Kafka or RabbitMQ) and topics. The backend services are registered as event publishers and they publish events on specific topics. Client applications are registered as event subscribers to respective topics, to receive those events published by the publisher services. Upon receiving the events, the client performs the required processing and displays it to the user.

Security, rate limiting, throttling, monetization and analytics are some of the important factors that an organization should focus on when exposing their core business functions as APIs. In order to address these, an enterprise must select the right API management solution. However, since async APIs and REST APIs are conceptually different, several unique challenges arise when using a conventional system for asynchronous APIs. These include incompatibilities with existing security mechanisms and throttling policies, and problems around capturing analytics data. Handling these challenges via a proper API management solution that fully supports event-driven APIs is a must.

## Securing Event-Driven APIs

API security can be categorized into authentication and authorization. Authentication describes who can access which resource, while authorization describes whether the authenticated user can perform the specific task. In conventional REST APIs, users can be authenticated using user credentials, access tokens, certificate-based authentication, etc. Also, each resource can also be protected with scopes and each API invocation can be protected too. However, in asynchronous APIs, since there are only topics to which the clients and services are subscribed to and the communication occurs through a dedicated messaging backbone, it is a challenging task to secure APIs.

One possible approach to handle this challenge is by authenticating during the initial HTTP communication. For example, we can secure the initial WebSocket handshake (via HTTP) before creating the connection. It is also possible to enforce authorization by defining whether the client can publish any events or not.