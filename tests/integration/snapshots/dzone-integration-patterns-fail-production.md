# 6 Integration Patterns That Look Good on Paper and What Happens When They Hit Production

In most enterprise systems, integrations don’t fail immediately. They fail slowly. Everything works fine at first, APIs respond quickly, workflows look clean, and dependencies seem manageable. Then traffic grows, systems evolve, and edge cases appear. That’s when the cracks start to show.

In my experience, these failures are rarely caused by tools. They come from how [integration patterns](https://dzone.com/articles/integration-patterns-in-microservices-world) are applied without considering real-world conditions like latency, retries, partial failures, and security boundaries.

Instead of covering every possible pattern, I’ll focus on six patterns that show up in almost every architecture, along with what they look like in practice and where they tend to break.

## **1. Request–Response (Synchronous APIs)**

One system calls another and waits for a response before continuing.

**Example**: A mobile app calls an [API](https://dzone.com/articles/everything-you-should-know-about-apis) to check order status and displays the result immediately.

**Where it works**:

* Real-time user interactions
* Simple lookups
* Fast, predictable systems

**Whe****re it fails**:

* When the API calls multiple downstream systems
* When one dependency becomes slow
* When used for long-running operations (like invoice processing)

**Example failure**:

An order API calls inventory -> pricing -> shipping -> tax systems. One slow system delays everything and causes timeouts.