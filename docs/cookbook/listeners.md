[Event Listeners](../components/README.md#powered-by-events) are a core part of Athena's architecture that allows tapping into specific events within the life-cycle of each request.  Custom events can also be defined, dispatched, and listened upon.  See the related [EventDispatcher](../components/event_dispatcher.md) component for more information.

## JWT Security

Currently Athena does not have any built in abstractions related to authentication or authorization.  This feature is planned and will be implemented at some point in the future.  Until then however, we can define a security listener that implements our authentication logic via listening on the [action](../components/README.md#1-request-event) event which includes a reference to the original [HTTP::Request](https://crystal-lang.org/api/HTTP/Request.html) object.

```crystal
# Define and register a listener to handle authenticating requests.
@[ADI::Register]
struct SecurityListener
  include AED::EventListenerInterface

  def self.subscribed_events : AED::SubscribedEvents
    AED::SubscribedEvents{
      # Specify that we want to listen on the request event
      # with slightly higher priority just because
      ART::Events::Request => 10,
    }
  end

  # Define a `#call` method scoped to the `Request` event.
  def call(event : ART::Events::Request, _dispatcher : AED::EventDispatcherInterface) : Nil
    # Don't execute the listener logic for endpoints that we consider to be public.
    # Again this'll eventually be handled by the security related abstractions.
    if event.request.method == "POST" && {"/user", "/login"}.includes? event.request.path
      return
    end

    # Return a 401 error if the token is missing or malformed
    raise ART::Exceptions::Unauthorized.new "Missing bearer token", "Bearer realm=\"My App\"" unless (auth_header = event.request.headers.get?("authorization").try &.first) && auth_header.starts_with? "Bearer "

    # Get the JWT token from the Bearer header
    token = auth_header.lchop "Bearer "

    begin
      # Validate the token using the `crystal-community/jwt` shard.
      body = JWT.decode token, ENV["SECRET"], :hs512
    rescue decode_error : JWT::DecodeError
      # Throw a 401 error if the JWT token is invalid
      raise ART::Exceptions::Unauthorized.new "Invalid token", "Bearer realm=\"My App\""
    end
  end
end
```

At this point any request that is not "public" will invoke our listener that ensures the request has a valid [JWT](https://jwt.io) `Bearer` token.  From here we can go a step further and define a service that can be used to hold a reference to the current user, such that it could be accessed within other controllers, listeners, or services.

```crystal
@[ADI::Register]
class UserStorage
  # Use a `!` to define both nilable and not nilable getters.
  # Assume that you have a `User` object that represents a user within your application.
  property! user : User
end
```

We can then inject this service into our security listener to set the current user.

```crystal
@[ADI::Register]
struct SecurityListener
  ...

  # Define our initializer for DI to inject the user storage.
  def initialize(@user_storage : UserStorage); end

  # Define a `#call` method scoped to the `Request` event.
  def call(event : ART::Events::Request, _dispatcher : AED::EventDispatcherInterface) : Nil
    ...

    # Set the user in user storage, looking it up from the DB
    # based on a `user_id` claim within the JWT token.
    @user_storage.user = User.find body[0]["user_id"]
  end
end
```

From here, it would be up to the developer to implement a way to authorize the user now that they have been authenticated and are accessible within the application.  One option could be to utilize the [Custom Annotations](../components/config.md#custom-annotations) as a means to "tag" controller actions with specific "levels" of security; then add another `#call` method to the security listener to listen on the [action](../components/README.md#2-action-event) event which exposes the [ART::Action][Athena::Routing::Action] related to the current request from which the annotations could be read off of.

!!! page
    This example is a modified version of the one used as part of the [JSON API Blog Tutorial](https://dev.to/blacksmoke16/creating-a-json-api-with-athena--granite-510i) blog post.

## Pagination

Generic pagination can be implemented via listening on the [view](../components/README.md#4-view-event) event which exposes the value returned via the related controller action.  We can then define a `Paginated` [Custom Annotation](../components/config.md#custom-annotations) that can be applied to controller actions to have them be paginated via the listener.

```crystal
# Define our configuration annotation with the default pagination values.
# These values can be overridden on a per endpoint basis.
ACF.configuration_annotation Paginated, page : UInt32 = 1, per_page : UInt32 = 100, max_per_page : UInt32 = 1000

# Define and register our listener that will handle paginating the response.
@[ADI::Register]
struct PaginationListener
  include AED::EventListenerInterface

  private PAGE_QUERY_PARAM     = "page"
  private PER_PAGE_QUERY_PARAM = "per_page"

  def self.subscribed_events : AED::SubscribedEvents
    AED::SubscribedEvents{
      # We want this to run before anything else so that
      # future listeners are working with the paginated data.
      ART::Events::View => 255,
    }
  end

  def call(event : ART::Events::View, dispatcher : AED::EventDispatcherInterface) : Nil
    # Return if the endpoint is not paginated.
    return unless (pagination = event.request.action.annotation_configurations[Paginated]?)

    # Return if the action result is not able to be paginated.
    return unless (action_result = event.action_result).is_a? Indexable

    request = event.request

    # Determine pagination values; first checking the request's query parameters,
    # using the default values in the `Paginated` object if not provided.
    page = request.query_params[PAGE_QUERY_PARAM]?.try &.to_i || pagination.page
    per_page = request.query_params[PER_PAGE_QUERY_PARAM]?.try &.to_i || pagination.per_page

    # Raise an exception if `per_page` is higher than the max.
    raise ART::Exceptions::BadRequest.new "Query param 'per_page' should be '#{pagination.max_per_page}' or less." if per_page > pagination.max_per_page

    # Paginate the resulting data.
    # In the future a more robust pagination service could be injected
    # that could handle types other than `Indexable`, such as
    # ORM `Collection` objects.
    end_index = page * per_page
    start_index = end_index - per_page

    # Paginate and set the action's result.
    event.action_result = action_result[start_index...end_index]
  end
end

class ExampleController < ART::Controller
  @[ARTA::Get("values")]
  @[Paginated(per_page: 2)]
  def get_values : Array(Int32)
    (1..10).to_a
  end
end

ART.run

# GET /values # => [1, 2]
# GET /values?page=2 # => [3, 4]
# GET /values?per_page=3 # => [1, 2, 3]
# GET /values?per_page=3&page=2 # => [4, 5, 6]
```

## Static Files

```crystal
@[ADI::Register]
struct StaticFileListener
  include AED::EventListenerInterface

  # This could be part of the config object.
  private PUBLIC_DIR = Path.new("assets").expand

  def self.subscribed_events : AED::SubscribedEvents
    AED::SubscribedEvents{
      ART::Events::Request => 256,
    }
  end

  # In the future you'd probably use this to resolve your related configuration obj.
  # def initialize(@configuration_resolver : ACF::ConfigurationResolverInterface); end

  def call(event : ART::Events::Request, _dispatcher : AED::EventDispatcherInterface) : Nil
    # TODO: Fallback if the request method isn't intended for files.
    return unless event.request.method.in? "GET", "HEAD"

    original_path = event.request.path
    is_dir_path = original_path.ends_with? '/'
    request_path = URI.decode original_path

    # File path cannot contains '\0' (NUL) because all filesystem I know
    # don't accept '\0' character as file name.
    if request_path.includes? '\0'
      raise ART::Exceptions::BadRequest.new "File path cannot contain NUL bytes."
    end

    request_path = Path.posix request_path
    expanded_path = request_path.expand "/"

    file_path = PUBLIC_DIR.join expanded_path.to_kind Path::Kind.native

    is_dir = Dir.exists? file_path
    is_file = !is_dir && File.exists? file_path

    if request_path != expanded_path || is_dir && !is_dir_path
      redirect_path = expanded_path
      if is_dir && !is_dir_path
        redirect_path = expanded_path.join ""
      end

      return event.response = ART::RedirectResponse.new redirect_path.to_s
    elsif is_file
      headers = HTTP::Headers.new

      last_modified = self.modification_time(file_path)
      self.add_cache_headers(headers, last_modified)

      if self.cache_request?(event.request, headers, last_modified)
        return event.response = ART::Response.new status: HTTP::Status::NOT_MODIFIED
      end

      headers["content-type"] = MIME.from_filename(file_path.to_s, "application/octet-stream")

      # Checks if pre-gzipped file can be served
      if event.request.headers.includes_word?("accept-encoding", "gzip")
        gz_file_path = "#{file_path}.gz"

        if File.exists?(gz_file_path) &&
           # Allow small time drift. In some file systems, using `gz --keep` to
           # compress the file will keep the modification time of the original file
           # but truncating some decimals
           last_modified - modification_time(gz_file_path) < 1.millisecond
          file_path = gz_file_path

          headers["content-Encoding"] = "gzip"
        end
      end

      headers["content-length"] = File.size(file_path).to_s

      event.response = ART::StreamedResponse.new headers: headers do |io|
        File.open(file_path) do |file|
          IO.copy file, io
        end
      end
    end
  end

  private def add_cache_headers(response_headers : HTTP::Headers, last_modified : Time) : Nil
    response_headers["etag"] = self.etag(last_modified)
    response_headers["last-modified"] = HTTP.format_time(last_modified)
  end

  private def cache_request?(request : HTTP::Request, response_headers : HTTP::Headers, last_modified : Time) : Bool
    # According to RFC 7232:
    # A recipient must ignore If-Modified-Since if the request contains an If-None-Match header field
    if if_none_match = request.if_none_match
      match = {"*", response_headers["etag"]}
      if_none_match.any? { |etag| match.includes?(etag) }
    elsif if_modified_since = request.headers["if-modified-since"]?
      header_time = HTTP.parse_time(if_modified_since)
      # File mtime probably has a higher resolution than the header value.
      # An exact comparison might be slightly off, so we add 1s padding.
      # Static files should generally not be modified in subsecond intervals, so this is perfectly safe.
      # This might be replaced by a more sophisticated time comparison when it becomes available.
      !!(header_time && last_modified <= header_time + 1.second)
    else
      false
    end
  end

  private def etag(modification_time)
    %{W/"#{modification_time.to_unix}"}
  end

  private def modification_time(file_path)
    File.info(file_path).modification_time
  end
end
```