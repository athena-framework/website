[Param Converters][Athena::Routing::ParamConverterInterface] allow applying custom logic in order to convert one or more primitive request parameter into a more complex type.

## DB

In a REST API, endpoints usually contain a reference to the `id` of the object in question; e.x. `GET /user/10`.  A useful converter would be able to extract this ID from the path, lookup the related entity, and provide that object directly to the controller action.  This reduces the boilerplate associated with doing a DB lookup within every controller action.  It also makes testing easier as it abstract the logic of _how_ that object is resolved from what should be done to it.

This example uses the `Granite` ORM, but should work with others.  Alternatively a [DTO](https://en.wikipedia.org/wiki/Data_transfer_object) may be used to keep (de)serialization and validation logic separate from the actual models.

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
    # Nothing else to do except return the releated article.
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

## Request Body

Similar to the `DB` converter, another common practice is deserializing a request's body into an object.

> **NOTE:** This examples uses the `Granite` ORM, but should work with others.

```crystal
# Define an register our param converter as a service.
@[ADI::Register]
struct RequestBody < ART::ParamConverterInterface
  # Define a customer configuration for this converter.
  # This allows us to provide a `entity` field within the annotation
  # in order to define _what_ entity should be queried for.
  configuration entity : Granite::Base.class

  # Inject the serializer and validator into our converter.
  def initialize(
      @serializer : ASR::SerializerInterface,
      @validator : AVD::Validator::ValidatorInterface,
  ); end

  # :inherit:
  def apply(request : HTTP::Request, configuration : Configuration) : Nil
    # Be sure to handle any possible exceptions here to return more helpful errors to the client.
    raise ART::Exceptions::BadRequest.new "Request body is empty." unless body = request.body

    # Deserialize the object, based on the type provided in the annotation.
    object = @serializer.deserialize configuration.entity, body, :json

    # Validate the object if it is validatable.
    if object.is_a? AVD::Validatable
      errors = @validator.validate object
      raise AVD::Exceptions::ValidationFailed.new errors unless errors.empty?
    end

    # Add the resolved object to the request's attributes.
    request.attributes.set configuration.name, object, configuration.entity
  end
end

# Make the compiler happy when we want to allow any Granite entity to be deserializable.
class Granite::Base
  include ASR::Model
end

class Article < Granite::Base
  connection "default"
  table "articles"

  column id : Int64, primary: true
  column title : String
end

@[ARTA::Prefix("article")]
class ExampleController < ART::Controller
  @[ARTA::Post(path: "")]
  @[ARTA::View(status: :created)]
  @[ARTA::ParamConverter("article", converter: RequestBody, model: Article)]
  def new_article(article : Article) : Article
    # Since we have an actual `Article` instance, we can simply save and return the article.
    article.save
    article
  end
end
```

We can now easily save new entities, and be assured they are valid by running validations as well within our converter.  However what about updating an entity?  The [Serializer][Athena::Serializer] component has the concept of [Object Constructors][Athena::Serializer::ObjectConstructorInterface] that determine how a new object is constructed during deserialization.  This feature allows updated values to be *applied* to an existing object as opposed to either needing to create a whole new object from the request data or manually handle applying those changes.

```crystal
# Define a custom `ASR::ObjectConstructorInterface` to allow sourcing the model from the database
# as part of `PUT` requests, and if the type is a `Granite::Base`.
#
# Alias our service to `ASR::ObjectConstructorInterface` so ours gets injected instead.
@[ADI::Register(alias: ASR::ObjectConstructorInterface)]
class DBObjectConstructor
  include Athena::Serializer::ObjectConstructorInterface

  # Inject `ART::RequestStore` in order to have access to the current request.
  # Also inject `ASR::InstantiateObjectConstructor` to act as our fallback constructor.
  def initialize(@request_store : ART::RequestStore, @fallback_constructor : ASR::InstantiateObjectConstructor); end

  # :inherit:
  def construct(navigator : ASR::Navigators::DeserializationNavigatorInterface, properties : Array(ASR::PropertyMetadataBase), data : ASR::Any, type)
    # Fallback on the default object constructor if the type is not a `Granite` model.
    unless type <= Granite::Base
      return @fallback_constructor.construct navigator, properties, data, type
    end

    # Fallback on the default object constructor if the current request is not a `PUT`.
    unless @request_store.request.method == "PUT"
      return @fallback_constructor.construct navigator, properties, data, type
    end

    # Lookup the object from the database; assume the object has an `id` property.
    entity = type.find data["id"].as_i64

    # Return a `404` error if no record exists with the given ID.
    raise ART::Exceptions::NotFound.new "An item with the provided ID could not be found." unless entity

    # Apply the updated properties to the retrieved record
    entity.apply navigator, properties, data

    # Return the entity
    entity
  end
end
```

The [Validator][Athena::Validator] component could also be injected into the param converter to run validations after deserialzing an object.
