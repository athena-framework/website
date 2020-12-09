Athena does not have any other dependencies outside of [Crystal](https://crystal-lang.org) and [Shards](https://crystal-lang.org/reference/the_shards_command/index.html).
It is designed in such a way to be non-intrusive, and not require a strict organizational convention in regards to how a project is setup;
this allows it to use a minimal amount of setup boilerplate while not preventing it for more complex projects.

## Installation

Add the dependency to your `shard.yml`:

```yaml
dependencies:
  athena:
    github: athena-framework/athena
    version: ~> 0.12.0
```

Run `shards install`.  This will install Athena and its required dependencies.

## Usage

Athena has a goal of being easy to start using for simple use cases, while still allowing flexibility/customizability for larger more complex use cases.

### Routing

Athena is a MVC based framework, as such, the logic to handle a given route is defined in an [ART::Controller](https://athena-framework.github.io/athena/Athena/Routing/Controller.html) class.

```crystal
require "athena"

# Define a controller
class ExampleController < ART::Controller
  # Define an action to handle the related route
  @[ART::Get("/")]
  def index : String
    "Hello World"
  end

  # The macro DSL can also be used
  get "/" do
    "Hello World"
  end
end

# Run the server
ART.run

# GET / # => Hello World
```
Annotations applied to the methods are used to define the HTTP method this method handles, such as [ART::Get](https://athena-framework.github.io/athena/Athena/Routing/Get.html) or [ART::Post](https://athena-framework.github.io/athena/Athena/Routing/Post.html).  A macro DSL also exists to make them a bit less verbose;
[ART::Controller.get](https://athena-framework.github.io/athena/Athena/Routing/Controller.html#get(path,*args,**named_args,&)-macro) or [ART::Controller.post](https://athena-framework.github.io/athena/Athena/Routing/Controller.html#post(path,*args,**named_args,&)-macro).  The [ART::Route](https://athena-framework.github.io/athena/Athena/Routing/Route.html) annotation can also be used to define custom `HTTP` methods.

Controllers are simply classes and routes are simply methods.  Controllers and actions can be documented/tested as you would any Crystal class/method.

### Route Parameters

Arguments are converted to their expected types if possible, otherwise an error response is automatically returned.
The values are provided directly as method arguments, thus preventing the need for `env.params.url["name"]` and any boilerplate related to it. Just like normal method arguments, default values can be defined. The method's return type adds some type safety to ensure the expected value is being returned.

```crystal
require "athena"

class ExampleController < ART::Controller
  @[ART::Get("/add/:value1/:value2")]
  def add(value1 : Int32, value2 : Int32, negative : Bool = false) : Int32
    sum = value1 + value2
    negative ? -sum : sum
  end
end

ART.run

# GET /add/2/3               # => 5
# GET /add/5/5?negative=true # => -10
# GET /add/foo/12            # => {"code":400,"message":"Required parameter 'value1' with value 'foo' could not be converted into a valid 'Int32'"}
```

[ART::QueryParam](https://athena-framework.github.io/athena/Athena/Routing/QueryParam.html) and [ART::RequestParam](https://athena-framework.github.io/athena/Athena/Routing/RequestParam.html)s are defined via annotations and map directly to the method's arguments.  See the related annotation docs for more information.

```crystal
require "athena"

class ExampleController < ART::Controller
  @[ART::Get("/")]
  @[ART::QueryParam("page", requirements: /\d{2}/)]
  def index(page : Int32) : Int32
    page
  end
end

ART.run

# GET /          # => {"code":422,"message":"Parameter 'page' of value '' violated a constraint: 'This value should not be null.'\n"}
# GET /?page=10  # => 10
# GET /?page=bar # => {"code":400,"message":"Required parameter 'page' with value 'bar' could not be converted into a valid 'Int32'."}
# GET /?page=5   # => {"code":422,"message":"Parameter 'page' of value '5' violated a constraint: 'Parameter 'page' value does not match requirements: (?-imsx:^(?-imsx:\\d{2})$)'\n"}
```

Restricting an action argument to [HTTP::Request](https://crystal-lang.org/api/HTTP/Request.html) will provide the raw request object.
This approach is fine for simple or one-off endpoints, however for more complex/common request data processing, it is suggested to create
a [Param Converter](./advanced_usage.md#param-converters).

```crystal
require "athena"

class ExampleController < ART::Controller
  @[ART::Post("/data")]
  def data(request : HTTP::Request) : String?
    request.body.try &.gets_to_end
  end
end

ART.run

# POST /data body: "foo--bar" # => "foo--bar"
```

#### Returning Raw Data

An [ART::Response](https://athena-framework.github.io/athena/Athena/Routing/Response.html) can be used to fully customize the response; such as returning a specific status code, adding some one-off headers.

```crystal
require "athena"
require "mime"

class ExampleController < ART::Controller
  # A GET endpoint returning an `ART::Response`.
  # Can be used to return raw data, such as HTML or CSS etc, in a one-off manner.
  @[ART::Get("/index")]
  def index : ART::Response
    ART::Response.new "<h1>Welcome to my website!</h1>", headers: HTTP::Headers{"content-type" => MIME.from_extension(".html")}
  end
end

ART.run

# GET /index # => "<h1>Welcome to my website!</h1>"
```

An [ART::Events::View](https://athena-framework.github.io/athena/Athena/Routing/Events/View.html) is emitted if the returned value is _NOT_ an [ART::Response](https://athena-framework.github.io/athena/Athena/Routing/Response.html).  By default, non [ART::Response](https://athena-framework.github.io/athena/Athena/Routing/Response.html)s are JSON serialized.
However, this event can be listened on to customize how the value is serialized.

##### Streaming Response

By default `ART::Response` content is written all at once to the response's `IO`.  However in some cases the content may be too large to fit into memory.  In this case an [ART::StreamedResponse](https://athena-framework.github.io/athena/Athena/Routing/StreamedResponse.html) may be used to stream the content back to the client.

```crystal
require "athena"
require "mime"

class ExampleController < ART::Controller
  @[ART::Get(path: "/users")]
  def users : ART::Response
    ART::StreamedResponse.new headers: HTTP::Headers{"content-type" => "application/json; charset=UTF-8"} do |io|
      User.all.to_json io
    end
  end
end

ART.run

# GET /athena/users" # => [{"id":1,...},...]
```

### URL Generation

A common use case, especially when rendering `HTML`, is generating links to other routes based on a set of provided parameters.  Parameters that do not map to a controller action argument are added as query params.

```crystal
require "athena"

class ExampleController < ART::Controller
  # Define a route to redirect to, explicitly naming this route `add`.
  # The default route name is controller + method down snake-cased; e.x. `example_controller_add`.
  @[ART::Get("/add/:value1/:value2", name: "add")]
  def add(value1 : Int32, value2 : Int32, negative : Bool = false) : Int32
    sum = value1 + value2
    negative ? -sum : sum
  end

  # Define a route that redirects to the `add` route with fixed parameters.
  @[ART::Get("/")]
  def redirect : ART::RedirectResponse
    # Generate a link to the other route.
    url = self.generate_url "add", value1: 8, value2: 2

    url # => /add/8/2

    # Redirect to the user to the generated url.
    self.redirect url

    # Or could have used a method that does both
    self.redirect_to_route "add", value1: 8, value2: 2
  end
end

ART.run

# GET / # => 10
```

See [ART::URLGeneratorInterface](https://athena-framework.github.io/athena/Athena/Routing/URLGeneratorInterface.html) in the API Docs for more details.

### Error Handling

Exception handling in Athena is similar to exception handling in any Crystal program, with the addition of a new unique exception type, [ART::Exceptions::HTTPException](https://athena-framework.github.io/athena/Athena/Routing/Exceptions/HTTPException.html).
Custom `HTTP` errors can also be defined by inheriting from [ART::Exceptions::HTTPException](https://athena-framework.github.io/athena/Athena/Routing/Exceptions/HTTPException.html) or a child type.
A use case for this could be allowing additional data/context to be included within the exception.

Non [ART::Exceptions::HTTPException](https://athena-framework.github.io/athena/Athena/Routing/Exceptions/HTTPException.html) exceptions are represented as a `500 Internal Server Error`.

When an exception is raised, Athena emits the [ART::Events::Exception](https://athena-framework.github.io/athena/Athena/Routing/Events/Exception.html) event to allow an opportunity for it to be handled.
By default these exceptions will return a `JSON` serialized version of the exception, via [ART::ErrorRenderer](https://athena-framework.github.io/athena/Athena/Routing/ErrorRenderer.html), that includes the message and code; with the proper response status set.
If the exception goes unhandled, i.e. no listener sets an [ART::Response](https://athena-framework.github.io/athena/Athena/Routing/Response.html).  By default, non [ART::Response](https://athena-framework.github.io/athena/Athena/Routing/Response.html) on the event, then the request is finished and the exception is re-raised.

```crystal
require "athena"

class ExampleController < ART::Controller
  get "divide/:num1/:num2", num1 : Int32, num2 : Int32, return_type: Int32 do
    num1 // num2
  end

  get "divide_rescued/:num1/:num2", num1 : Int32, num2 : Int32, return_type: Int32 do
    num1 // num2
    # Rescue a non `ART::Exceptions::HTTPException`
  rescue ex : DivisionByZeroError
    # in order to raise an `ART::Exceptions::HTTPException` to provide a better error message to the client.
    raise ART::Exceptions::BadRequest.new "Invalid num2:  Cannot divide by zero"
  end
end

ART.run

# GET /divide/10/0          # => {"code":500,"message":"Internal Server Error"}
# GET /divide_rescued/10/0  # => {"code":400,"message":"Invalid num2:  Cannot divide by zero"}
# GET /divide_rescued/10/10 # => 1
```

### Logging

Logging is handled via Crystal's [Log](https://crystal-lang.org/api/Log.html) module.  Athena logs when a request matches a controller action, as well as any exception.  This of course can be augmented with additional application specific messages.

```bash
2020-12-06T17:20:12.334700Z   INFO - Server has started and is listening at http://0.0.0.0:3000
2020-12-06T17:20:17.163953Z   INFO - athena.routing: Matched route /divide/10/0 -- uri: "/divide/10/0", method: "GET", path_params: {"num2" => "0", "num1" => "10"}, query_params: {}
2020-12-06T17:20:17.280199Z  ERROR - athena.routing: Uncaught exception #<DivisionByZeroError:Division by 0> at ../../../../../../usr/lib/crystal/int.cr:138:7 in 'check_div_argument'
Division by 0 (DivisionByZeroError)
  from ../../../../../../usr/lib/crystal/int.cr:138:7 in 'check_div_argument'
  from ../../../../../../usr/lib/crystal/int.cr:102:5 in '//'
  from src/athena.cr:151:5 in 'get_divide__num1__num2'
  from ../../../../../../usr/lib/crystal/primitives.cr:255:3 in 'execute'
  from src/route_handler.cr:80:5 in 'handle_raw'
  from src/route_handler.cr:14:21 in 'handle'
  from src/athena.cr:127:9 in '->'
  from ../../../../../../usr/lib/crystal/primitives.cr:255:3 in 'process'
  from ../../../../../../usr/lib/crystal/http/server.cr:513:5 in 'handle_client'
  from ../../../../../../usr/lib/crystal/http/server.cr:468:13 in '->'
  from ../../../../../../usr/lib/crystal/primitives.cr:255:3 in 'run'
  from ../../../../../../usr/lib/crystal/fiber.cr:92:34 in '->'
  from ???

2020-12-06T17:20:18.979050Z   INFO - athena.routing: Matched route /divide_rescued/10/0 -- uri: "/divide_rescued/10/0", method: "GET", path_params: {"num2" => "0", "num1" => "10"}, query_params: {}
2020-12-06T17:20:18.980397Z   WARN - athena.routing: Uncaught exception #<Athena::Routing::Exceptions::BadRequest:Invalid num2:  Cannot divide by zero> at src/athena.cr:159:5 in 'get_divide_rescued__num1__num2'
Invalid num2:  Cannot divide by zero (Athena::Routing::Exceptions::BadRequest)
  from src/athena.cr:159:5 in 'get_divide_rescued__num1__num2'
  from ../../../../../../usr/lib/crystal/primitives.cr:255:3 in 'execute'
  from src/route_handler.cr:80:5 in 'handle_raw'
  from src/route_handler.cr:14:21 in 'handle'
  from src/athena.cr:127:9 in '->'
  from ../../../../../../usr/lib/crystal/primitives.cr:255:3 in 'process'
  from ../../../../../../usr/lib/crystal/http/server.cr:513:5 in 'handle_client'
  from ../../../../../../usr/lib/crystal/http/server.cr:468:13 in '->'
  from ../../../../../../usr/lib/crystal/primitives.cr:255:3 in 'run'
  from ../../../../../../usr/lib/crystal/fiber.cr:92:34 in '->'
  from ???

2020-12-06T17:20:21.993811Z   INFO - athena.routing: Matched route /divide_rescued/10/10 -- uri: "/divide_rescued/10/10", method: "GET", path_params: {"num2" => "10", "num1" => "10"}, query_params: {}
```

##### Customization

By default Athena utilizes the default [Log::Formatter](https://crystal-lang.org/api/Log/Formatter.html) and [Log::Backend](https://crystal-lang.org/api/Log/Backend.html)s Crystal defines.  This of course can be customized via interacting with Crystal's [Log](https://crystal-lang.org/api/Log.html) module. It is also possible to control what exceptions, and with what severity, exceptions will be logged by redefining the `log_exception` method within [ART::Listeners::Error](https://athena-framework.github.io/athena/Athena/Routing/Listeners/Error.html).
