## DB

The [Serializer][Athena::Serializer] component also has the concept of [Object Constructors][Athena::Serializer::ObjectConstructorInterface] that determine how a new object is constructed during deserialization.  A use case could be retrieving the object from the database as part of a `PUT` request in order to apply the deserialized data onto it.  This would allow it to retain the PK, any timestamps, or [ASRA::ReadOnly][ASRA::ReadOnly] values.

!!!note
    This example uses the `Granite` ORM, but should work with others.

```crystal
# Define a custom `ASR::ObjectConstructorInterface` to allow
# sourcing the model from the database as part of `PUT`
# requests, and if the type is a `Granite::Base`.
#
# Alias our service to `ASR::ObjectConstructorInterface`
# so ours gets injected instead.
@[ADI::Register(alias: ASR::ObjectConstructorInterface)]
class DBObjectConstructor
  include Athena::Serializer::ObjectConstructorInterface

  # Inject `ART::RequestStore` in order to have access to
  # the current request. Also inject `ASR::InstantiateObjectConstructor`
  # to act as our fallback constructor.
  def initialize(
    @request_store : ART::RequestStore,
    @fallback_constructor : ASR::InstantiateObjectConstructor
  ); end

  # :inherit:
  def construct(navigator : ASR::Navigators::DeserializationNavigatorInterface, properties : Array(ASR::PropertyMetadataBase), data : ASR::Any, type)
    # Fallback on the default object constructor if
    # the type is not a `Granite` model.
    unless type <= Granite::Base
      return @fallback_constructor.construct navigator, properties, data, type
    end

    # Fallback on the default object constructor if 
    # the current request is not a `PUT`.
    unless @request_store.request.method == "PUT"
      return @fallback_constructor.construct navigator, properties, data, type
    end

    # Lookup the object from the database; 
    # assume the object has an `id` property.
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

This object constructor could then be used with the [RequestBody](param_converters.md#request-body) param converter, assuming the `type` of the configuration value is `Granite::Base.class`.  For example:

```crystal
@[ADI::Register]
struct RequestBody < ART::ParamConverterInterface
  # Define a customer configuration for this converter.
  # This allows us to provide a `entity` field within the annotation
  # in order to define _what_ entity should be queried for.
  configuration entity : Granite::Base.class
  
  # ...
end

# Make the compiler happy when we want to allow any
# Granite entity to be deserializable via the Serializer component.
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
  @[ARTA::ParamConverter("article", converter: RequestBody, entity: Article)]
  def new_article(article : Article) : Article
    # Since we have an actual `Article` instance with the updates
    # from the JSON payload already applied,
    # we can simply save and return the article.
    article.save
    article
  end
end
```

