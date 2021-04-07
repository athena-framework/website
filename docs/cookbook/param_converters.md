[Param Converters][Athena::Routing::ParamConverterInterface] allow applying custom logic in order to convert one or more primitive request arguments into a more complex type.

## Request Body

A core part of any API is consuming a request body in order to create/update some entity or to perform some action.  The [Getting Started](../getting_started/README.md#request-parameter) docs showed how this could be done by using the raw request object.  However a more robust approach would be to define a generic & reusable [Param Converter][Athena::Routing::ParamConverterInterface] that would be able to deserialize the request body into an object, run any validations defined on it, then provide the object to the controller action.

Ideally this object would be a [DTO](https://en.wikipedia.org/wiki/Data_transfer_object), but could also be an `ORM` entity for simple use cases.

```crystal
require "athena"

# Define our base type.
# DTO objects are defined as structs as they
# are more performant and should be immutable.
abstract struct DTO
  include ASR::Model
end

# Define a User DTO object to represent the creation of a new user entity.
struct UserCreate < DTO
  # Include some modules to tell Athena this type can be deserialized
  # via the Serializer component and validated via the Valdiator component.
  include AVD::Validatable
  include ASR::Serializable

  # Assert the user's name is not blank.
  @[Assert::NotBlank]
  getter first_name : String

  # Assert the user's name is not blank.
  @[Assert::NotBlank]
  getter last_name : String

  # Assert the user's email is not blank and is valid.
  @[Assert::NotBlank]
  @[Assert::Email(:html5)]
  getter email : String
end

# Create and register a param converter that'll allow our DTO object
# to be provided directly as a controller action argument.
@[ADI::Register]
struct RequestBody < ART::ParamConverterInterface
  # Allows specifying which DTO type should be
  # deserialized via the ParamConvter annotation.
  configuration type : DTO.class

  # Inject the related services for deserialization and validation.
  def initialize(
    @serializer : ASR::SerializerInterface,
    @validator : AVD::Validator::ValidatorInterface
  ); end

  # :inherit:
  def apply(request : HTTP::Request, configuration : Configuration) : Nil
    # Ensure the request body isn't empty.
    raise ART::Exceptions::BadRequest.new "Request body is empty." unless body = request.body

    # Deserialize the request body into a DTO object.
    object = @serializer.deserialize configuration.type, body, :json

    # If the object is validatable, run its validations,
    # raising a 422 if it is not.
    if object.is_a? AVD::Validatable
      errors = @validator.validate object
      raise AVD::Exceptions::ValidationFailed.new errors unless errors.empty?
    end

    # All the desrialized object to be provided directly within the controller action.
    request.attributes.set configuration.name, object, configuration.type
  end
end

class UserController < ART::Controller
  # Define a controller action that will be responsible for creating the new user record.
  @[ARTA::Post("/user")]
  @[ARTA::View(status: :created)]
  @[ARTA::ParamConverter("user_create", converter: RequestBody, type: UserCreate)]
  def new_user(user_create : UserCreate) : UserCreate
    # Use the provided UserCreate instance to create an actual User DB record.
    # For purposes of this example, just return the instance.

    user_create
  end
end

ART.run
```

Making a request to our `/user` endpoint with the following payload:

```json
{
  "first_name": "George",
  "last_name": "",
  "email": "dietrich.app"
}
```

Would return the response:

```json
{
  "code": 422,
  "message": "Validation failed",
  "errors": [
    {
      "property": "last_name",
      "message": "This value should not be blank.",
      "code": "0d0c3254-3642-4cb0-9882-46ee5918e6e3"
    },
    {
      "property": "email",
      "message": "This value is not a valid email address.",
      "code": "ad9d877d-9ad1-4dd7-b77b-e419934e5910"
    }
  ]
}
```

While a valid request would return: 

```json
{
  "first_name": "George",
  "last_name": "Dietrich",
  "email": "george@dietrich.app"
}
```

The `RequestBody` converter provides a generic reusable way to convert the request body's `JSON` payload into objects that can have complex deserialization/validation logic via the [Serializer][Athena::Serializer] and [Validator][Athena::Validator] components respectively.

The Serializer component also has the concept of [Object Constructors][Athena::Serializer::ObjectConstructorInterface] that determine how a new object is constructed during deserialization.  Checkout the [cookbook](object_constructors.md#db) for how could be used when working with raw DB entities.

## DB

In a REST API, endpoints usually contain a reference to the `id` of the object in question; e.x. `GET /user/10`.  A useful converter would be able to extract this ID from the path, lookup the related entity, and provide that object directly to the controller action.  This reduces the boilerplate associated with doing a DB lookup within every controller action.  It also makes testing easier as it abstract the logic of _how_ that object is resolved from what should be done to it.

!!!note
    This example uses the `Granite` ORM, but should work with others.

```crystal
# Define an register our param converter as a service.
@[ADI::Register]
struct DBConverter < ART::ParamConverterInterface
  # Define a customer configuration for this converter.
  # This allows us to provide a `entity` field within the annotation
  # in order to define _what_ entity should be queried for.
  configuration entity : Granite::Base.class

  # :inherit:
  #
  # Be sure to handle any possible exceptions here to return more helpful errors to the client.
  def apply(request : HTTP::Request, configuration : Configuration) : Nil
    # Grab the `id` path parameter from the request's attributes as an Int32.
    primary_key = request.attributes.get "id", Int32

    # Raise a `404` error if a record with the provided ID does not exist.
    # This assumes there is a `.find` method on the related entity class.
    raise ART::Exceptions::NotFound.new "An item with the provided ID could not be found" unless entity = configuration.entity.find primary_key

    # Set the resolved entity within the request's attributes
    # with a key matching the name of the argument within the converter annotation.
    request.attributes.set configuration.name, model, configuration.entity
  end
end

class Article < Granite::Base
  connection "default"
  table "articles"

  column id : Int64, primary: true
  column title : String
end

@[ARTA::Prefix("article")]
class ExampleController < ART::Controller
  @[ARTA::Get("/:id")]
  @[ARTA::ParamConverter("article", converter: DBConverter, entity: Article)]
  def get_article(article : Article) : Article
    # Nothing else to do except return the related article.
    article
  end
end

# Run the server
ART.run

# GET /article/1    # => {"id":1,"title":"Article A"}
# GET /article/5    # => {"id":5,"title":"Article E"}
# GET /article/-123 # => {"code":404,"message":"An item with the provided ID could not be found."}
```

Tada.  We now testable, reusable logic to provide database objects directly as arguments to our controller action.  Since the entity class is specified on the annotation, the actual converter can be reused for multiple actions and multiple entity classes.
