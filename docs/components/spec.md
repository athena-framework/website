Athena strongly suggests following the [SOLID](https://en.wikipedia.org/wiki/SOLID) design principles;
especially the [Dependency inversion principle](https://en.wikipedia.org/wiki/Dependency_inversion_principle) in order to create types that are easy to test.  See the [Dependency Injection](../components/dependency_injection.md) component for a more detailed look.

If these principles are followed then any of the previously mentioned concepts, param converters, event listeners, and/or controllers,
can easily be unit tested on their own as you would any Crystal type, possibly utilizing [ART::Spec::TestCase](https://athena-framework.github.io/athena/Athena/Spec/TestCase.html) to provide helpful abstractions around common testing/helper logic for sets of common types.

However, Athena also comes bundled with [ART::Spec::APITestCase](https://athena-framework.github.io/athena/Athena/Routing/Spec/APITestCase.html) to allow for easily creating integration tests for [ART::Controller](https://athena-framework.github.io/athena/Athena/Routing/Controller.html)s.

```crystal
require "athena"
require "athena/spec"

class ExampleController < ART::Controller
  @[ART::QueryParam("negative")]
  @[ART::Get("/add/:value1/:value2")]
  def add(value1 : Int32, value2 : Int32, negative : Bool = false) : Int32
    sum = value1 + value2
    negative ? -sum : sum
  end
end

struct ExampleControllerTest < ART::Spec::APITestCase
  def test_add_positive : Nil
    self.request("GET", "/add/5/3").body.should eq "8"
  end

  def test_add_negative : Nil
    self.request("GET", "/add/5/3?negative=true").body.should eq "-8"
  end
end

# Run all test case tests.
ASPEC.run_all
```

Integration tests allow testing the full system, including event listeners, param converters, etc at once.
These tests do not utilize an [HTTP::Server](https://crystal-lang.org/api/HTTP/Server.html) which results in more performant specs.
