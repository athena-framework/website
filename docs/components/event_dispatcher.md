```crystal
require "athena"

@[ADI::Register]
struct CustomListener
  include AED::EventListenerInterface

  # Specify that we want to listen on the `Response` event.
  # The value of the hash represents this listener's priority;
  # the higher the value the sooner it gets executed.
  def self.subscribed_events : AED::SubscribedEvents
    AED::SubscribedEvents{
      ART::Events::Response => 25,
    }
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