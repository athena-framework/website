## Dependency Injection

Athena utilizes `Athena::DependencyInjection` to provide a service container layer.
DI allows controllers/other services to be decoupled from specific implementations.
This makes testing easier as test implementations of the dependencies can be used.

In Athena, most everything is a service that belongs to the container, which is unique to the current request.  The major benefit of this is it allows various types to be shared amongst the services.
For example, allowing param converters, controllers, etc. to have access to the current request via the `ART::RequestStore` service.

Another example would be defining a service to store a `UUID` to represent the current request, then using this service to include the UUID in the response headers.

```crystal
require "athena"
require "uuid"

@[ADI::Register]
struct RequestIDStore
  HEADER_NAME = "X-Request-ID"

  # Inject `ART::RequestStore` in order to have access to the current request's headers.
  def initialize(@request_store : ART::RequestStore); end

  property request_id : String? = nil do
    # Check the request store for a request.
    request = @request_store.request?

    # If there is a request and it has the Header,
    if request && request.headers.has_key? HEADER_NAME
      # use that ID.
      request.headers[HEADER_NAME]
    else
      # otherwise generate a new one.
      UUID.random.to_s
    end
  end
end

@[ADI::Register]
struct RequestIDListener
  include AED::EventListenerInterface

  def self.subscribed_events : AED::SubscribedEvents
    AED::SubscribedEvents{
      ART::Events::Response => 0,
    }
  end

  def initialize(@request_id_store : RequestIDStore); end

  def call(event : ART::Events::Response, dispatcher : AED::EventDispatcherInterface) : Nil
    # Set the request ID as a response header
    event.response.headers[RequestIDStore::HEADER_NAME] = @request_id_store.request_id
  end
end

class ExampleController < ART::Controller
  get "/" do
    ""
  end
end

ART.run

# GET / # => (`X-Request-ID => 07bda224-fb1d-4b82-b26c-19d46305c7bc` header)
```

The main benefit of having `RequestIDStore` and not doing `event.response.headers[RequestIDStore::HEADER_NAME] = UUID.random.to_s` directly is that the value could be used in other places.
Say for example you have a route that enqueues messages to be processed asynchronously.  The `RequestIDStore` could be inject into that controller/service in order to include the same `UUID`
within the message in order to expand tracing to async contexts.  Without DI, like in other frameworks, there would not be an easy to way to share the same instance of an object between
different types.  It also wouldn't be easy to have access to data outside the request context.

DI is also what "wires" everything together.  For example, say there is an external shard that defines a listener.  All that would be required to use that listener is install and require the shard,
DI takes care of the rest.  This is much easier and more flexible than needing to update code to add a new `HTTP::Handler` instance to an array.