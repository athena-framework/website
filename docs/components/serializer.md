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