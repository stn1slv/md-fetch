# More Control, Less Toil: Simplified Security and Policies in Kong Gateway 3.14

April 15, 2026

The best platform teams don't write glue code — they configure great infrastructure. But as API platform architectures get more complex, policy logic does not always fit into a one-size-fits-all model. Not only that, but security toil compounds with every new service, credential, and cloud provider added to the mix. Kong Gateway 3.14 addresses these challenges and more.

Here's what's new in 3.14:

* **Conditional Plugin Execution:** New condition field to specify additional conditions in order for the plugin to execute.
* **JWT Nodes for Datakit:** Support complex auth use cases with JWT Verify, Sign, and Decode operations in Datakit, no code required.
* **WebSocket Security & Observability:** OIDC, mTLS, and ACL authentication at the WebSocket handshake, with real-time metrics for connection health and session activity.
* **OpenID Token Exchange:** Transform, scope, and delegate tokens at the gateway via native OAuth 2.0 Token Exchange (RFC 8693).
* **Cloud-Native Auth Improvements:** Unified IAM authentication across AWS, Azure, and GCP — consistent cloud-native identity across your entire multi-cloud footprint.
* **OpenMeter Plugin:** Real-time metering and consumption-based billing policies for API and AI traffic, within Kong Konnect.

Read on for a deep dive into each of these capabilities and what they mean for your platform.

## Simplify complexity with conditional plugin execution

Managing gateway configurations at scale is harder than it looks. When a plugin needs to apply to most routes, but not all, teams could either duplicate configuration across routes and violate DRY (“Don’t Repeat Yourself”) principles, or write custom code to handle the exceptions. Neither scales well, and both create long-term maintenance debt.

With conditional plugin execution, users can now attach conditional expressions directly to any plugin, based on request attributes like headers, paths, or content types. The gateway evaluates these expressions in real-time and decides whether to run the plugin or bypass it entirely.

This means you can apply a single plugin broadly and let the expression handle the exceptions, keeping your configuration. Whether you're enforcing auth policies that shouldn't fire for internal traffic, scoping transformations to specific content types, or preventing a validation plugin from running in the wrong context, conditional execution gives you the granular control to do it right.

In 3.14 we’re adding this feature as a Beta release. Read more about how conditional plugin execution works and what you can do with it in [this blog](https://konghq.com/blog/engineering/conditional-policy-execution) and [our documentation](https://developer.konghq.com/gateway/configure-conditional-plugin-execution/).

## Build complex authentication policies with JWT nodes for Datakit

Kong has long supported a number of out-of-the-box plugins for both validating and generating JWT tokens, as well as using those tokens to authenticate callers.