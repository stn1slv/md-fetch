# MCP is everywhere, but don’t panic. Here’s why your existing APIs still matter.

Learn why APIs still matter in the age of Model Context Protocol (MCP), and how to balance traditional APIs and MCP for secure AI agents.

Everyone is excited for the promise of “Digital coworkers” in this agentic era. Model Context Protocol (MCP) is all anyone can talk about these days when it comes to agentic enablement. But what if you have spent the last decade building APIs for your organization? Do you have to throw out all that work and adopt the MCP-first strategy?

Before you throw the baby out with the bathwater, let’s first consider the multiple approaches to API and MCP integrations that might serve us as we are building agentic applications.

## APIs: The old, reliable bridge

An API is often described as a bridge that lets two systems talk to each other, but I find it more helpful to think of APIs as selections on a restaurant menu. The contents of each dish are clearly marked, so you know what you are getting. If you order beef, you won’t receive pasta. Just like a menu, APIs are predefined by humans and accompanied by documentation that can be reviewed before use.

APIs do not allow for speculation. For example, if you want customer data in your application, you use the customer endpoints from the API. Selecting the customer endpoints means that you will get what you’re looking for–in this example, customer data, not weather forecast data.

> “An API is often described as a bridge that lets two systems talk to each other, but I find it more helpful to think of APIs as selections on a restaurant menu.”

The useful part of APIs is that they are specific and tightly structured, requiring code to follow a defined construct. For example, well-designed REST APIs follow a clear pattern of verbs (what the system can do) and nouns (the components in the system). Clear verb examples are “get,” “create,” “delete,” and noun examples are “file,” “user,” “invoice”. This separation is done so that machines have prescriptive, controlled ways of interacting based on the semantics of the APIs.

Before AI agents, building client applications that leverage APIs required custom code that aligned directly to each specific API. An application can only interact with the endpoints it is explicitly told to use. AI agents, on the other hand, when given an endpoint, will repeatedly call it, trying to understand how it works until they get a successful response.

They learn the API, but sometimes with disastrous consequences. Agents have been shown to overcall endpoints, retrieve sensitive data, or retry APIs until they accidentally break something. Even worse, some agents have leaked API credentials, as in the instance of [OpenClaw API key leaks](https://www.bitsight.com/blog/openclaw-ai-security-risks-exposed-instances%23:~:text=The%2520traffic%2520included%2520prompt%2520injection,'ve%2520read%2520the%2520source.%25E2%2580%259D).

Even with this new agentic paradigm, APIs still have a role to play in delivering successful agents. For example, if you have private data that can improve an agent’s accuracy but is highly sensitive and requires complex authorization structures, an API can ensure controlled access to it. However, you need to carefully consider your API strategy for agents, because there is a cost… literally.

For example, if you have a complex API with many fields, you need to document exactly how to use it for the agent. The agent may also choose to start exploring other endpoints in the API.

Providing information on how to use the API, as well as the specific API parameters, is additional information that an agent will need to carry throughout their session, which means you are compounding the tokens spent on API information and taking up more space in the context window.

Instead of relying on detailed APIs, which can consume a significant number of tokens, consider using Model Context Protocol (MCP). MCP provides a lighter-weight, specification-based integration alternative for agents, helping conserve your tokens throughout the session.