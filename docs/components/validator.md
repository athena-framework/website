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

