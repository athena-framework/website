## Architecture



## Extensions

Athena comes bundled with some additional potentially useful components (shards).
Due to the nature of Crystal's build process, any types/methods that are not used, are not included in the resulting binary.
Thus if your project does not use any of these extensions, the resulting binary will be unchanged.
However by having them included by default, they are available and ready to go when/if the need arises.
It's also worth noting that these extra components are not Athena specific and can be used within any project/library outside of the Athena ecosystem.

These extensions register additional component specific types as services with the service container.
This allows them to be injected via DI into your `Athena::Routing` related types, such as controllers, param converters, and/or event listeners.

### Serialization

The `Athena::Serializer` component adds enhanced (de)serialization features.
See the API documentation for more detailed information, or [this forum post](https://forum.crystal-lang.org/t/athena-0-11-0/2627) for a quick overview.

Some highlights:

* `ASRA::Name` - Supporting different keys when deserializing versus serializing
* `ASRA::VirtualProperty` - Allow a method to appear as a property upon serialization
* `ASRA::IgnoreOnSerialize` - Allow a property to be set on deserialization, but should not be serialized (or vice versa)
* `ASRA::Expose` - Allows for more granular control over which properties should be (de)serialized
* `ASR::ExclusionStrategies` - Allows defining runtime logic to determine if a given property should be (de)serialized
* `ASR::ObjectConstructorInterface` - Determine how a new object is constructed during deserialization, e.x. sourcing an object from the DB

#### Dependency Injection

This extension registers the following types as services:

* `ASR::Serializer`

### Validation

The `Athena::Validator` component adds a robust/flexible validation framework.
See the API documentation for more detailed information, or [this forum post]() for a quick overview.

#### Dependency Injection

This extension registers the following types as services:

* `AVD::Validator::RecursiveValidator`

#### Custom Constraints

In addition to the general information for defining [Custom Constraints](https://athena-framework.github.io/validator/Athena/Validator/Constraint.html#custom-constraints),
the validator component defines a specific type for defining service based constraint validators: `AVD::ServiceConstraintValidator`.
This type should be inherited from instead of `AVD::ConstraintValidator` _IF_ the validator for your custom constraint needs to be a service, E.x.

```crystal
class Athena::Validator::Constraints::CustomConstraint < AVD::Constraint
  # ...

  @[ADI::Register]
  struct Validator < AVD::ServiceConstraintValidator
    def initialize(...); end

    # :inherit:
    def validate(value : _, constraint : AVD::Constraints::CustomConstraint) : Nil
      # ...
    end
  end
end
```