Athena also ships with some more advanced features to provide more flexibility/control for an application.
These features may not be required for a simple application; however as the application grows they may become more useful.

## Param Converters

[ART::ParamConverterInterface][Athena::Routing::ParamConverterInterface] s allow complex types to be supplied to an action via its arguments.
An example of this could be extracting the id from `/users/10`, doing a DB query to lookup the user with the PK of `10`, then providing the full user object to the action.
Param converters abstract any custom parameter handling that would otherwise have to be done in each action.

```crystal
require "athena"

@[ADI::Register]
struct MultiplyConverter < ART::ParamConverterInterface
  # :inherit:
  def apply(request : HTTP::Request, configuration : Configuration) : Nil
    arg_name = configuration.name

    return unless request.attributes.has? arg_name

    value = request.attributes.get arg_name, Int32
    request.attributes.set arg_name, value * 2, Int32
  end
end

class ParamConverterController < ART::Controller
  @[ARTA::Get(path: "/multiply/:num")]
  @[ARTA::ParamConverter("num", converter: MultiplyConverter)]
  def multiply(num : Int32) : Int32
    num
  end
end

ART.run

# GET / multiply/3 # => 6
```

## Middleware

Athena is an [event based framework](/components); meaning it emits [ART::Events][Athena::Routing::Events] that are acted upon internally to handle the request.  These same events can also be listened on by custom listeners, via [AED::EventListenerInterface][Athena::EventDispatcher::EventListenerInterface], in order to tap into the life-cycle of the request as a more flexible alternative to [HTTP::Handler](https://crystal-lang.org/api/HTTP/Handler.html)s.  An example use case of this could be: adding common headers, cookies, compressing the response, authentication, or even returning a response early like [ART::Listeners::CORS][Athena::Routing::Listeners::CORS].

See the [Event Dispatcher](/components/event_dispatcher) component for a more detailed look.

## Custom Annotations

User defined annotations may also be used to allow for more advanced logic; such as for [Pagination](/cookbook/listeners#pagination) or Rate limiting logic.  Custom annotations can be applied to a controller class and/or controller action method.  These annotations can then be accessed, including the data defined on them, within event listeners or anywhere the current request's [ART::Action][Athena::Routing::Action] is exposed.

See the [Config](/components/config#custom-annotations) component for a more detailed look.

## Validations

A common need when using any framework, is ensuring data flowing into the application is valid.  Athena comes bundled with various built in [Constraints][Athena::Validator::Constraints] that can be used to define the "rules" that an object must adhere to to be considered valid.

See the [Validator](/components/validator) component for a more details look.

## Testing

Each component in the Athena Framework includes a `Spec` module that includes common/helpful testing utilities/types for testing that specific component.  Athena itself defines some of its own testing types, mainly to allow for easisly integration testing [ART::Controller][Athena::Routing::Controller]s.

See the [Spec](/components/spec) component for a more detailed look.
