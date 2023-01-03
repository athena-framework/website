The [Athena::Routing][] component is used to determine which [ATH::Action][] should be handled via the incoming [ART::Request][].
It provides a robust, performant router without the limitations of other Crystal routers,
such as allowing multiple routes with the same path, using [parameter validation][Athena::Routing::Route--parameter-validation] and/or [sub-domain routing][Athena::Routing::Route--sub-domain-routing] to determine which one should be used.
See [ART::Route][Athena::Routing::Route] for more general information on the available features.

[Athena::Framework][] makes use of the routing component's [annotations][Athena::Routing::Annotations] to configure its routes.
All of the fields listed on [ARTA::Route][] are supported and are applied to the underlying [ART::Route][].
Some of them could be further integrated into the framework.

## URL Generation

The documentation mentioned in the getting started [documentation](../getting_started/README.md#url-generation) is specific to usages within the context of a request.
In this case, the scheme and hostname of a [ART::Generator::ReferenceType::ABSOLUTE_URL][] defaults to `http` and `localhost` respectively, if they could not be extracted from the request.
However, in cases where there is no request to use, such as within an [ACON::Command][], `http://localhost/` would always be the scheme and hostname of the generated URL.
[ATH::Parameters.configure][] can be used to customize this, as well as define a global path prefix when generating the URLs.
