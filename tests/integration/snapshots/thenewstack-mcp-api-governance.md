# The API portal is the clearest signal of whether your company can handle AI agents

In an interview with The New Stack, Kin Lane, API evangelist and co-founder of Naftiko, explains why mature API governance, OpenAPI specs, and developer portals decide which enterprises thrive in the agentic AI and MCP era.

**When I recently talked to Kin Lane, API evangelist and co-founder of [Naftiko](https://naftiko.io)**, I was repeatedly struck by the parallels between what we’re seeing with GenAI adoption and what we saw with the migration from private data centers to public cloud.

For cloud adoption, companies with strong psychological safety were better positioned to experiment and learn quickly because they already had safe-to-fail cultures. Organizations that had adopted domain-driven design were better placed to refactor monoliths to microservices. Those who had embraced some variation of XP or Agile were better able to rapidly implement their independently deployable microservices.

In other words, companies with strong engineering practices, coupled with a good culture, are best placed to handle transitions. That’s hardly surprising, but it does imply that a lack of investment in, for example, good-quality API documentation, puts a company at a distinct disadvantage.

## **MCP is just an API**

With agentic adoption, Lane tells *The New Stack*, the organizations that are best positioned are those that already have clean data pipelines, mature API management, cloud fluency, and working governance structures.

> “MCP is just an API — a long-lived HTTP connection serving up JSON. We’ve been doing that for years, it’s nothing new.”

This is because everything in software builds on top of pre-existing foundations. “MCP is just an API — a long-lived HTTP connection serving up JSON,” Lane says. “We’ve been doing that for years, it’s nothing new.” This means that artifacts such as OpenAPI specifications, AsyncAPI contracts, API gateways, developer portals, and documentation standards become the raw material of the agentic world.

An OpenAPI specification already describes your API’s operations, data shapes, and semantics. The same specification can be used to generate an MCP server. From there, agent skills that call those MCP servers can be derived from the same source.

“OpenAPI offers that kind of menu, that source of truth,” Lane says. “The skill is what you do with that menu — how do you order that burger? Open API will serve that menu to an agent.”

Organizations that have been rigorous about their OpenAPI definitions are sitting on a reusable asset that maps closely to what agents require. Those who have treated API specs as an afterthought or allowed them to drift from implementation reality will find the translation considerably harder.

## **Reversing the polarity of the neutron flow**

Lane describes a conceptual shift in how to think about what is new about the AI moment. For the past 15 years, API investment has been primarily outward-facing: Organizations expose resources via APIs so that developers can build on top of them. The consumer was a known quantity: a handful of partners, a developer community, perhaps a few million API calls at scale.

What changes with AI agents is the direction and volume of that pressure.