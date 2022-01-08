The [Athena::Routing][] component is used to determine which [ATH::Action][] should be handled via the incoming [ART::Request][].
It provides a robust, performant router without the limitations of other Crystal routers,
such as allowing multiple routes with the same path, using [parameter validation][Athena::Routing::Route--parameter-validation] and/or [sub-domain routing][Athena::Routing::Route--sub-domain-routing] to determine which one should be used.
See [ART::Route][] for more information.
