As mentiond in the [architecture](./README.md) section, Athena is an event based framework utilizing the [Event Dispatcher][Athena::EventDispatcher] component.

## Basic Usage

An event listener is defined by registering a service that includes [AED::EventListenerInterface][Athena::EventDispatcher::EventListenerInterface].  The type should also define a `self.subscribed_events` method that represents what [events][Athena::Routing::Events] it should be listening on.

```crystal
require "athena"

@[ADI::Register]
class CustomListener
  include AED::EventListenerInterface

  # Specify that we want to listen on the `Response` event.
  # The value of the hash represents this listener's priority;
  # the higher the value the sooner it gets executed.
  def self.subscribed_events : AED::SubscribedEvents
    AED::SubscribedEvents{ART::Events::Response => 25}
  end

  def call(event : ART::Events::Response, dispatcher : AED::EventDispatcherInterface) : Nil
    event.response.headers["FOO"] = "BAR"
  end
end

class ExampleController < ART::Controller
  get "/" do
    "Hello World"
  end
end

ART.run

# GET / # => Hello World (with `FOO => BAR` header)
```

!!! tip
    A single event listener may listen on multiple events.  Instance variables can be used to share state between the events.

## Custom Events

Custom events can also be defined and dispatched; either within a listener, or in another service by injecting [AED::EventDispatcherInterface][Athena::EventDispatcher::EventDispatcherInterface] and calling `#dispatch`.

```crystal
require "athena"

# Define a custom event
class MyEvent < AED::Event
  property value : Int32
  
  def initialize(@value : Int32); end
end

# Define a listener that listens our the custom event.
@[ADI::Register]
class CustomEventListener
  include AED::EventListenerInterface

  def self.subscribed_events : AED::SubscribedEvents
    AED::SubscribedEvents{MyEvent => 0}
  end

  def call(event : MyEvent, dispatcher : AED::EventDispatcherInterface) : Nil
    event.value *= 10
  end
end

# Register a controller as a service,
# injecting the event dispatcher to handle processing our value.
@[ADI::Register(public: true)]
class ExampleController < ART::Controller
  def initialize(@event_dispatcher : AED::EventDispatcherInterface); end
  
  @[ART::Get("/:value")]
  def get_value(value : Int32) : Int32
    event = MyEvent.new value
    
    @event_dispatcher.dispatch event
    
    event.value
  end
end

ART.run

# GET /10 # => 100
```
