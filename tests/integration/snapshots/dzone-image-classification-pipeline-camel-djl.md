# Building an Image Classification Pipeline With Apache Camel and Deep Java Library (DJL)

Image classification is now a key part of many applications. Whether you’re automating photo organization, filtering uploaded content, or enriching product catalogs with visual tags, knowing what’s in an image can be just as important as knowing what a user typed.

For Java developers, the challenge is familiar: most computer vision examples live in Python notebooks, while the systems that actually need image classification run on the JVM. Bridging that gap usually means standing up a separate Python microservice, managing REST calls, and dealing with serialization overhead. That’s a lot of ceremony for what should be a single processing step.

This tutorial will show you how to build an image classification pipeline in pure Java with [Apache Camel](https://dzone.com/refcardz/enterprise-integration) and the Deep Java Library (DJL). We’ll cover watching folders for new images, running classification with a pre-trained ResNet model, tidying up the predictions into clean reports, and routing results to output files, all while leaning on those trusty Enterprise Integration Patterns you’re probably already familiar with.

## **What You'll Learn**

By the time you’re done here, you’ll be comfortable with:

* Develop a file-based image classification pipeline using Apache Camel.
* Use a pre-trained ResNet image classification model via Camel’s DJL component.
* Understand the djl: URI syntax and model configuration for computer vision tasks in Apache Camel.
* Structure routes with content-based routing and multiple formatter beans.
* Run image classification locally using Java and Apache Camel, without external APIs or Python services.

## **Frameworks Used**

### Apache Camel

Apache Camel is an awesome open-source integration framework built on Enterprise Integration Patterns. It has great components for connecting systems, moving data, and orchestrating workflows using declarative routes.

In this project, we look at file ingestion, message transformation, content-based routing, bean integration, error handling, and output persistence.

### Deep Java Library (DJL)

DJL is a deep learning framework for Java that is engine-agnostic. It provides a high-level API for inference, training, and serving deep learning models right on the JVM.