# Content Analysis API Documentation
*Consolidated main text documentation of Content Analysis API compiled from docs.dataforseo.com*

---


### Overview
*Source: [https://docs.dataforseo.com/v3/content_analysis/overview/](https://docs.dataforseo.com/v3/content_analysis/overview/)*
### Content Analysis API: Overview

Content Analysis API is a robust source of data for brand monitoring, sentiment analysis, and citation management

Content Analysis API is designed to help you discover citations of the target keyword or brand and analyze the sentiments around it.

This API identifies the positive, negative, and neutral polarity in any text, and detects the following sentiment connotations: anger, happiness, love, sadness, share (desire to share content), and fun.

Content Analysis API currently has the following set of endpoints:

- [Search](https://docs.dataforseo.com/v3/content_analysis/search/live/) will find all citations for the target keyword and provide detailed information about each citation.
- [Summary](https://docs.dataforseo.com/v3/content_analysis/summary/live/) will give you a complete overview of citation data available for the target keyword.
- [Sentiment Analysis](https://docs.dataforseo.com/v3/content_analysis/sentiment_analysis/live/) will reveal granular citation stats by positive, negative, and neutral sentiment polarity and by sentiment connotations.
- [Rating Distribution](https://docs.dataforseo.com/v3/content_analysis/rating_distribution/live/) will return citation stats distribution by content rating.
- [Phrase Trends](https://docs.dataforseo.com/v3/content_analysis/phrase_trends/live/) will furnish you with detailed citation stats by date for a target keyword.
- [Category Trends](https://docs.dataforseo.com/v3/content_analysis/category_trends/live/) will supply you with citation trends by date in a target category.

Using the Search endpoint, you can specify the number of results you want to retrieve, filter, and sort them. We do not charge any fees for using data filtering or sorting rules.

The Search endpoint of Content Analysis API allows applying custom filtration to the dataset that will be retrieved. By using filters, you can effortlessly get exactly the data you need. For more information, please refer to [Filters in Content Analysis API.](https://docs.dataforseo.com/v3/content_analysis/filters/)

To find answers on common questions about DataForSEO Content Analysis API and find guidance on efficient use of its features, [visit our Help Center.](https://dataforseo.com/help-center/category/content-analysis-api)

##### Methods

DataForSEO Content Analysis API supports only the Live method of data retrieval. It doesn’t require making separate POST and GET requests to the corresponding endpoints and delivers instant results. You can send up to 2000 API calls per minute. Contact us if you want to raise the limit.

##### Cost

The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/content-analysis) page. You can check your spending in your [account dashboard](https://app.dataforseo.com/api-access) or by making a separate call to [the User Data endpoint.](https://docs.dataforseo.com/v3/appendix/user_data/?php)

You can test Content Analysis API for free using DataForSEO [Sandbox.](https://docs.dataforseo.com/v3/appendix/sandbox/)

---


### Filters
*Source: [https://docs.dataforseo.com/v3/content_analysis/filters/](https://docs.dataforseo.com/v3/content_analysis/filters/)*
#### Filters for Content Analysis API

Here you will find all the necessary information about filters that can be used with Content Analysis API endpoints.

Note that filters are associated with a certain object in the `result` array, and should be specified accordingly. You can learn more about how to use filters in [this help center article](https://dataforseo.com/help-center/using-filters).

Pricing

Your account will not be charged for using this API

GEThttps://api.dataforseo.com/v3/content_analysis/available_filters

You will receive the full list of filters by calling this API. You can also download the full list of possible filters [by this link.](https://cdn.dataforseo.com/v3/available_filters.php?api=content_analysis)

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total tasks cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the parameters passed in the URL of the GET request* |
| **`result`** | array | *array of results*<br>contains the full list of available parameters that can be used for data filtration<br>the parameters are grouped by the endpoint they can be used with |

Below you will find a detailed description of the structure that should be used to specify filters for Content Analysis API. You will also find the types of parameters that can be used with each endpoint, and examples of pre-made filters.

**Description of the fields:**

| Field name | Type | Description |
| --- | --- | --- |
| `filters` | array | *array of results filtering parameters*<br>filters have the following structure:<br>**[`filered_field`, `filter_operator`, `filter_value`]**<br>**you can add several filters at once (8 filters maximum)**<br>if you add more than one filter, you must set a logical operator `and`, `or` between the conditions<br>example:<br>`[["domain_rank",">", "800"],"and",["content_info.connotation_types.negative",">","0.9"]]` |
| `filtered_field` | str | *fields that support filtration*<br>note that some filtered_fields have the following structure: `"content_info.$parameter_field"` or `"content_info.$results_array.$parameter_field"`<br>examples:<br>`"domain_rank"`<br>`"content_info.title"`<br>`"content_info.sentiment_connotations.fun"`<br> |
| `filter_operator` | str | *operator in the filter*<br>available filter operators:<br>• if **`num`**: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>• if **`str`**: `like`, `not_like`, `=`, `<>`, `regex`, `not_regex`, `in`, `not_in`, `match`, `not_match`<br>• if **`array.str`**: `has`, `has_not`<br>• if **`array.num`**: `has`, `has_not`<br>• if **`time`**: `<`, `>`<br>note: `time` should be specified in the format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2021-01-29 15:02:37 +00:00`<br>if you specify `in` or `not_in` operator, the `$filter_value` should be specified as an array<br>example:<br>`["domain_rank","in",[100,500]]`<br>**Note:** the maximum limit for the number of characters you can specify in `regex` and `not_regex` is **1000** |
| `filter_value` | | *filtering value*<br>values specified in the `filter_value` should match the format of the specified `filtered_field` |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The list of available filtration parameters:

---


### Locations
*Source: [https://docs.dataforseo.com/v3/content_analysis/locations/](https://docs.dataforseo.com/v3/content_analysis/locations/)*
#### List of Locations for Content Analysis API

Pricing

Your account will not be charged for using this API

GEThttps://api.dataforseo.com/v3/content_analysis/locations

You will receive the list of locations by this API call.

##### **Note:** All locations in Russia and Belarus are no longer supported across all DataForSEO services due to the invasion of Ukraine.

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total tasks cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the parameters passed in the URL of the GET request* |
| **`result`** | array | *array of results* |
| `location_name` | string | *full name of the location* |
| `country_iso_code` | string | *ISO country code of the location* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Languages
*Source: [https://docs.dataforseo.com/v3/content_analysis/languages/](https://docs.dataforseo.com/v3/content_analysis/languages/)*
#### List of Languages for Content Analysis API

Pricing

Your account will not be charged for using this API

GEThttps://api.dataforseo.com/v3/content_analysis/languages

You will receive the list of languages by calling this API.
 
As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total tasks cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the parameters passed in the URL of the GET request* |
| ** `result`** | array | *array of results* |
| `language_name` | string | *language name* |
| `language_code` | string | *language code according to [ISO 639-1](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes)* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Categories
*Source: [https://docs.dataforseo.com/v3/content_analysis/categories/](https://docs.dataforseo.com/v3/content_analysis/categories/)*
#### List of Categories for Content Analysis API

We use Google product and service categories. This endpoint will provide you with the full list of available categories.
You can also download the `CSV` file [by this link.](https://developers.google.com/google-ads/api/data/tables/productsservices.csv)

GEThttps://api.dataforseo.com/v3/content_analysis/categories

Pricing

Your account will not be charged for using this API

By calling this API you will receive the list of categories supported by Content Analysis API.
As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information about available categories.

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total tasks cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the parameters passed in the URL of the GET request* |
| **`result`** | array | *array of results* |
| `category_code` | integer | *category code* |
| `category_name` | string | *full name of the category* |
| `category_code_parent` | integer | *the code of the superordinate category*<br>example:<br>`"category_code": 10178,<br>"category_name": "Apparel Accessories",<br>"category_code_parent": 10021`<br>where `category_code_parent`<br>corresponds to:<br>`"category_code": 10178,<br>"category_name": "Apparel Accessories"` |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Search
*Source: [https://docs.dataforseo.com/v3/content_analysis/search/live/](https://docs.dataforseo.com/v3/content_analysis/search/live/)*
#### Content Analysis – Search API

This endpoint will provide you with detailed citation data available for the target keyword.

POSThttps://api.dataforseo.com/v3/content_analysis/search/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/content-analysis) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute.

You can specify the number of results you want to retrieve, filter and sort them.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `keyword` | string | *target keyword*<br>**required field**<br>UTF-8 encoding<br>the keywords will be converted to a lowercase format;<br>**Note**: to match an exact phrase instead of a stand-alone keyword, use double quotes and backslashes;<br>example:<br>`"keyword": "\"tesla palo alto\""`<br>learn more about rules and limitations of `keyword` and `keywords` fields in DataForSEO APIs in this [Help Center article](https://dataforseo.com/help-center/rules-and-limitations-of-keyword-and-keywords-fields-in-dataforseo-apis) |
| `keyword_fields` | object | *target keyword fields and target keywords*<br>optional field<br>use this parameter to filter the dataset by keywords that certain fields should contain;<br>fields you can specify: `title`, `main_title`, `previous_title`, `snippet`<br>you can indicate several fields;<br>**Note**: to match an exact phrase instead of a stand-alone keyword, use double quotes and backslashes;<br>example:<br>`"keyword_fields": {<br> "snippet": "\"logitech mouse\"",<br> "main_title": "sale"<br>}` |
| `page_type` | array | *target page types*<br>optional field<br>use this parameter to filter the dataset by page types<br>possible values:<br>`"ecommerce"`, `"news"`, `"blogs"`, `"message-boards"`, `"organization"`<br> |
| `search_mode` | string | *results grouping type*<br>optional field<br>possible grouping types:<br>`as_is` – returns all citations for the target `keyword`<br>`one_per_domain` – returns one citation of the `keyword` per domain<br>default value: `as_is` |
| `limit` | integer | *the maximum number of returned citations*<br>optional field<br>default value: `100`<br>maximum value: `1000` |
| `filters` | array | *array of results filtering parameters*<br>optional field<br>**you can add several filters at once (8 filters maximum)**<br>you should set a logical operator `and`, `or` between the conditions<br>the following operators are supported:<br>`regex`, `not_regex`, `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`, `like`,`not_like`, `match`, `not_match`<br>you can use the `%` operator with `like` and `not_like` to match any string of zero or more characters<br>example:<br>`["country","=", "US"]`<br>`[["domain_rank",">",800],"and",["content_info.connotation_types.negative",">",0.9]]`<br>`[["domain_rank",">",800],<br>"and",<br>[["page_types","has","ecommerce"],<br>"or",<br>["content_info.text_category","has",10994]]]`<br>for more information about filters, please refer to [Content Analysis API – Filters](https://docs.dataforseo.com/v3/content_analysis/filters) |
| `order_by` | array | *results sorting rules*<br>optional field<br>you can use the same values as in the `filters` array to sort the results<br>possible sorting types:<br>`asc` – results will be sorted in the ascending order<br>`desc` – results will be sorted in the descending order<br>you should use a comma to set up a sorting type<br>example:<br>`["content_info.sentiment_connotations.anger,desc"]`<br>default rule:<br>`["content_info.sentiment_connotations.anger,desc"]`<br>**note that you can set no more than three sorting rules in a single request**<br>you should use a comma to separate several sorting rules<br>example:<br>`["content_info.sentiment_connotations.anger,desc","keyword_data.keyword_info.cpc,desc"]` |
| `offset` | integer | *offset in the results array of returned citations*<br>optional field<br>default value: `0`<br>if you specify the `10` value, the first ten citations in the results array will be omitted and the data will be provided for the successive citations<br>**Note:** we recommend using this parameter only when retrieving up to 10,000 results<br>for retrieving over 10,000 results, use the `offset_token` instead. |
| `offset_token` | string | *offset token for subsequent requests*<br>optional field<br>provided in the identical field of the response to each request;<br>use this parameter to avoid timeouts while trying to obtain over 10,000 results in a single request;<br>by specifying the unique `offset_token` value from the response array, you will get the subsequent results of the initial task;<br>`offset_token` values are unique for each subsequent task<br>**Note:** if the `offset_token` is specified in the request, all other parameters except `limit` will not be taken into account when processing a task<br>learn more about this parameter on our [Help Center](https://dataforseo.com/help-center/what-is-the-difference-between-the-offset-and-offset_token-parameters#offset_token) |
| `rank_scale` | string | *defines the scale used for calculating and displaying the `domain_rank`, and `url_rank` values*<br>optional field<br>you can use this parameter to choose whether rank values are presented on a 0–100 or 0–1000 scale<br>possible values:<br>`one_hundred` — rank values are displayed on a 0–100 scale<br>`one_thousand` — rank values are displayed on a 0–1000 scale<br>default value: `one_thousand`<br>learn more about how this parameter works in [this Help Center article](https://dataforseo.com/help-center/using-the-rank_scale-parameter-in-content-analysis-api) |
| `tag` | string | *user-defined task identifier*<br>optional field<br>*the character limit is 255*<br>you can use this parameter to identify the task and match it with the result<br>you will find the specified `tag` value in the `data` object of the response |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)<br>**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total tasks cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task *<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `offset_token` | string | *offset token for subsequent requests*<br>you can use the string provided in this field to get the subsequent results of the initial task;<br>**note:** `offset_token` values are unique for each subsequent task |
| `total_count` | integer | *total amount of results in our database relevant to your request* |
| `items_count` | integer | *the number of results returned in the `items` array* |
| `**items**` | array | *contains citations and related data* |
| `type` | string | *type of element = **‘content_analysis_search’*** |
| `url` | string | *URL where the citation was found* |
| `domain` | string | *domain name* |
| `main_domain` | string | *main domain* |
| `url_rank` | integer | *rank of the `url`*<br>this value is based on backlink data for the given URL from DataForSEO Backlink Index;<br>`url_rank` is calculated based on the method for node ranking in a linked database – a principle used in the original Google PageRank algorithm<br>learn more about the metric and how it is calculated in [this help center article](https://dataforseo.com/help-center/what_is_rank_in_backlinks_api) |
| `spam_score` | string | *backlink spam score of the `url`*<br>this value is based on backlink data for the given URL from DataForSEO Backlink Index;<br>learn more about how the metric is calculated on [this help center page](https://dataforseo.com/help-center/what-is-spam-score-and-how-is-it-calculated) |
| `domain_rank` | string | *rank of the `domain`*<br>this value is based on backlink data for the given domain from DataForSEO Backlink Index;<br>`domain_rank` is calculated based on the method for node ranking in a linked database – a principle used in the original Google PageRank algorithm<br>learn more about the metric and how it is calculated in [this help center article](https://dataforseo.com/help-center/what_is_rank_in_backlinks_api) |
| `fetch_time` | string | *date and time when our crawler visited the page*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2017-01-24 13:20:59 +00:00` |
| `country` | string | *country code of the domain registration*<br>to obtain a full list of available countries, refer to the [Locations](https://docs.dataforseo.com/v3/content_analysis/locations/) endpoint |
| `language` | string | *main language of the domain*<br>to obtain a full list of available languages, refer to the [Languages](https://docs.dataforseo.com/v3/content_analysis/languages/) endpoint |
| `score` | string | *citation prominence score*<br>this value is based on `url_rank`, `domain_rank`, `keyword` presence in `title`, `main_title`, `url`, `snippet`<br>the higher the `score`, the more value the related citation has |
| `page_category` | array | *contains all relevant page categories*<br>product and service categories relevant for the page<br>to obtain a full list of available categories, refer to the [Categories](https://docs.dataforseo.com/v3/content_analysis/categories/) endpoint |
| `page_types` | array | *page types* |
| `ratings` | array | *ratings found on the page*<br>all ratings found on the page based on microdata |
| `social_metrics` | array | *social media engagement metrics*<br>data on social media interactions associated with the content based on website embeds developed and supported by social media platforms |
| `**content_info**` | object | *contains data on citations from the given `url`* |
| `content_type` | string | *type of content*<br>example:<br>`page_content`, `comment` |
| `title` | string | *title of the result* |
| `main_title` | string | *page title* |
| `previous_title` | string | *title of the previous content block* |
| `level` | integer | *`title` heading level*<br>indicates h-tag level from `1` (top) to `6` (bottom) |
| `author` | string | *author of the content* |
| `snippet` | string | *content snippet* |
| `snippet_length` | integer | *character length of the snippet* |
| `social_metrics` | array | *social media engagement metrics*<br>data on social media interactions associated with the content based on website embeds developed and supported by social media platforms |
| `highlighted_text` | string | *highlighted text from the `snippet`* |
| `language` | string | *content language*<br>to obtain a full list of available languages, refer to the [Languages](https://docs.dataforseo.com/v3/content_analysis/languages/) endpoint |
| `sentiment_connotations` | object | *sentiment connotations*<br>contains sentiments (emotional reactions) related to the given citation and probability index per each sentiment<br>possible sentiment connotations: `anger`, `happiness`, `love`, `sadness`, `share`, `fun` |
| `connotation_types` | object | *connotation types*<br>contains types of sentiments (sentiment polarity) related to the given citation and probability index per each sentiment type<br>possible sentiment connotation types: `positive`, `negative`, `neutral` |
| `text_category` | array | *text category*<br>to obtain a full list of available categories, refer to the [Categories](https://docs.dataforseo.com/v3/content_analysis/categories/) endpoint |
| `date_published` | string | *date and time when the content was published*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2017-01-24 13:20:59 +00:00` |
| `content_quality_score` | integer | *content quality score*<br>this value is calculated based on the number of words, sentences and characters the content contains |
| `semantic_location` | string | *semantic location*<br>indicates semantic element in HTML where the target keyword citation is located<br>example:<br>`article`, `header` |
| `rating` | object | *content rating*<br>rating related to `content_info` |
| `name` | string | *rating name*<br>here you can find the following elements: `Max5`, `Percents`, `CustomMax` |
| `rating_value` | integer | *the value of the rating* |
| `max_rating_value` | integer | *maximum value for the rating `name`* |
| `rating_count` | integer | *number of votes* |
| `relative_rating` | float | *relative rating* |
| `group_date` | string | *citation group date and time*<br>indicates content publication date or date and time when our crawler visited the page for the first time;<br>this field can be used to group citations by date and display citation trends;<br>date and time are provided in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2017-01-24 13:20:59 +00:00` |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Summary
*Source: [https://docs.dataforseo.com/v3/content_analysis/summary/live/](https://docs.dataforseo.com/v3/content_analysis/summary/live/)*
#### Content Analysis – Summary API

This endpoint will provide you with an overview of citation data available for the target keyword.

POSThttps://api.dataforseo.com/v3/content_analysis/summary/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/content-analysis) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute.

You can specify the number of results you want to retrieve, filter and sort them.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `keyword` | string | *target keyword*<br>**required field**<br>UTF-8 encoding<br>the keywords will be converted to a lowercase format;<br>**Note**: to match an exact phrase instead of a stand-alone keyword, use double quotes and backslashes;<br>example:<br>`"keyword": "\"tesla palo alto\""`<br>learn more about rules and limitations of `keyword` and `keywords` fields in DataForSEO APIs in this [Help Center article](https://dataforseo.com/help-center/rules-and-limitations-of-keyword-and-keywords-fields-in-dataforseo-apis) |
| `keyword_fields` | object | *target keyword fields and target keywords*<br>optional field<br>use this parameter to filter the dataset by keywords that certain fields should contain;<br>fields you can specify: `title`, `main_title`, `previous_title`, `snippet`<br>you can indicate several fields;<br>**Note**: to match an exact phrase instead of a stand-alone keyword, use double quotes and backslashes;<br>example:<br>`"keyword_fields": {<br> "snippet": "\"logitech mouse\"",<br> "main_title": "sale"<br>}` |
| `page_type` | array | *target page types*<br>optional field<br>use this parameter to filter the dataset by page types<br>possible values:<br>`"ecommerce"`, `"news"`, `"blogs"`, `"message-boards"`, `"organization"`<br> |
| `internal_list_limit` | integer | *maximum number of elements within internal arrays*<br>optional field<br>you can use this field to limit the number of elements within the following arrays:<br>`top_domains`<br>`text_categories`<br>`page_categories`<br>`countries`<br>`languages`<br>default value: `1`<br>maximum value: `20` |
| `positive_connotation_threshold` | float | *positive connotation threshold*<br>optional field<br>specified as the probability index threshold for positive sentiment related to the citation content<br>if you specify this field, `connotation_types` object in the response will only contain data on citations with `positive` sentiment probability more than or equal to the specified value<br>possible values: from `0` to `1`<br>default value: `0.4` |
| `sentiments_connotation_threshold` | float | *sentiment connotation threshold*<br>optional field<br>specified as the probability index threshold for sentiment connotations related to the citation content<br>if you specify this field, `sentiment_connotations` object in the response will only contain data on citations where the<br>probability per each sentiment is more than or equal to the specified value<br>possible values: from `0` to `1`<br>default value: `0.4` |
| `initial_dataset_filters` | array | *initial dataset filtering parameters*<br>optional field<br>initial filtering parameters that apply to fields in the [Search endpoint](https://docs.dataforseo.com/v3/content_analysis/search/live/?bash)<br>**you can add several filters at once (8 filters maximum)**<br>you should set a logical operator `and`, `or` between the conditions<br>the following operators are supported:<br>`regex`, `not_regex`, `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`, `like`,`not_like`, `has`, `has_not`<br>you can use the `%` operator with `like` and `not_like` to match any string of zero or more characters<br>example:<br>`["domain","<>", "logitech.com"]`<br>`[["domain","<>","logitech.com"],"and",["content_info.connotation_types.negative",">",1000]]`<br>`[["domain","<>","logitech.com"]],<br>"and",<br>[["content_info.connotation_types.negative",">",1000],<br>"or",<br>["content_info.text_category","has",10994]]]`<br>for more information about filters, please refer to [Content Analysis API – Filters](https://docs.dataforseo.com/v3/content_analysis/filters)<br>learn more about the initial dataset filters in [this help center article.](https://dataforseo.com/help-center/what-are-the-initial-dataset-filters-and-how-do-they-work) |
| `rank_scale` | string | *defines the scale used for calculating and displaying the `rank` values*<br>optional field<br>you can use this parameter to choose whether rank values are presented on a 0–100 or 0–1000 scale<br>possible values:<br>`one_hundred` — rank values are displayed on a 0–100 scale<br>`one_thousand` — rank values are displayed on a 0–1000 scale<br>default value: `one_thousand`<br>learn more about how this parameter works in [this Help Center article](https://dataforseo.com/help-center/using-the-rank_scale-parameter-in-content-analysis-api) |
| `tag` | string | *user-defined task identifier*<br>optional field<br>*the character limit is 255*<br>you can use this parameter to identify the task and match it with the result<br>you will find the specified `tag` value in the `data` object of the response |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)<br>**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total tasks cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task *<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `type` | string | *type of element = **‘content_analysis_summary’*** |
| `total_count` | integer | *total amount of results in our database relevant to your request* |
| `rank` | integer | *rank of all URLs citing the `keyword`*<br>normalized sum of ranks of all URLs citing the target `keyword` |
| `top_domains` | array | *top domains citing the target keyword*<br>contains objects with top domains citing the target keword and citation count per each domain |
| `sentiment_connotations` | object | *sentiment connotations*<br>contains sentiments (emotional reactions) related to the target keyword citation and the number of citations per each sentiment<br>possible sentiment connotations: `anger`, `happiness`, `love`, `sadness`, `share`, `fun` |
| `connotation_types` | object | *connotation types*<br>contains types of sentiments (sentiment polarity) related to the keyword citation and citation count per each sentiment type<br>possible sentiment connotation types: `positive`, `negative`, `neutral` |
| `text_categories` | array | *text categories*<br>contains objects with text categories and citation count in each text category<br>to obtain a full list of available categories, refer to the [Categories](https://docs.dataforseo.com/v3/content_analysis/categories/) endpoint |
| `page_categories` | array | *page categories*<br>contains objects with page categories and citation count in each page category<br>to obtain a full list of available categories, refer to the [Categories](https://docs.dataforseo.com/v3/content_analysis/categories/) endpoint |
| `page_types` | object | *page types*<br>contains page types and citation count per each page type |
| `countries` | object | *countries*<br>contains countries and citation count in each country<br>to obtain a full list of available countries, refer to the [Locations](https://docs.dataforseo.com/v3/content_analysis/locations/) endpoint |
| `languages` | object | *languages*<br>contains languages and citation count in each language<br>to obtain a full list of available languages, refer to the [Languages](https://docs.dataforseo.com/v3/content_analysis/languages/) endpoint |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Sentiment Analysis
*Source: [https://docs.dataforseo.com/v3/content_analysis/sentiment_analysis/live/](https://docs.dataforseo.com/v3/content_analysis/sentiment_analysis/live/)*
#### Content Analysis – Sentiment Analysis API

This endpoint will provide you with sentiment analysis data for the citations available for the target keyword.

POSThttps://api.dataforseo.com/v3/content_analysis/sentiment_analysis/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/content-analysis) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute. The maximum number of requests that can be sent simultaneously is limited to 30.

You can specify the number of results you want to retrieve, filter and sort them.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `keyword` | string | *target keyword*<br>**required field**<br>UTF-8 encoding<br>the keywords will be converted to a lowercase format;<br>**Note**: to match an exact phrase instead of a stand-alone keyword, use double quotes and backslashes;<br>example:<br>`"keyword": "\"tesla palo alto\""`<br>learn more about rules and limitations of `keyword` and `keywords` fields in DataForSEO APIs in this [Help Center article](https://dataforseo.com/help-center/rules-and-limitations-of-keyword-and-keywords-fields-in-dataforseo-apis) |
| `keyword_fields` | object | *target keyword fields and target keywords*<br>optional field<br>use this parameter to filter the dataset by keywords that certain fields should contain;<br>fields you can specify: `title`, `main_title`, `previous_title`, `snippet`<br>you can indicate several fields;<br>**Note**: to match an exact phrase instead of a stand-alone keyword, use double quotes and backslashes;<br>example:<br>`"keyword_fields": {<br> "snippet": "\"logitech mouse\"",<br> "main_title": "sale"<br>}` |
| `page_type` | array | *target page types*<br>optional field<br>use this parameter to filter the dataset by page types<br>possible values:<br>`"ecommerce"`, `"news"`, `"blogs"`, `"message-boards"`, `"organization"`<br> |
| `internal_list_limit` | integer | *maximum number of elements within internal arrays*<br>optional field<br>you can use this field to limit the number of elements within the following arrays:<br>`top_domains`<br>`text_categories`<br>`page_categories`<br>`countries`<br>`languages`<br>default value: `1`<br>maximum value: `20` |
| `positive_connotation_threshold` | float | *positive connotation threshold*<br>optional field<br>specified as the probability index threshold for positive sentiment related to the citation content<br>if you specify this field, `connotation_types` object in the response will only contain data on citations with `positive` sentiment probability more than or equal to the specified value<br>possible values: from `0` to `1`<br>default value: `0.4` |
| `sentiments_connotation_threshold` | float | *sentiment connotation threshold*<br>optional field<br>specified as the probability index threshold for sentiment connotations related to the citation content<br>if you specify this field, `sentiment_connotations` object in the response will only contain data on citations where the probability per each sentiment is more than or equal to the specified value<br>possible values: from `0` to `1`<br>default value: `0.4` |
| `initial_dataset_filters` | array | *initial dataset filtering parameters*<br>optional field<br>initial filtering parameters that apply to fields in the [Search endpoint](https://docs.dataforseo.com/v3/content_analysis/search/live/?bash)<br>**you can add several filters at once (8 filters maximum)**<br>you should set a logical operator `and`, `or` between the conditions<br>the following operators are supported:<br>`regex`, `not_regex`, `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`, `like`,`not_like`, `has`, `has_not`, `match`, `not_match`<br>you can use the `%` operator with `like` and `not_like` to match any string of zero or more characters<br>example:<br>`["domain","<>", "logitech.com"]`<br>`[["domain","<>","logitech.com"],"and",["content_info.connotation_types.negative",">",1000]]`<br>`[["domain","<>","logitech.com"]],<br>"and",<br>[["content_info.connotation_types.negative",">",1000],<br>"or",<br>["content_info.text_category","has",10994]]]`<br>for more information about filters, please refer to [Content Analysis API – Filters](https://docs.dataforseo.com/v3/content_analysis/filters)<br>learn more about the initial dataset filters in [this help center article.](https://dataforseo.com/help-center/what-are-the-initial-dataset-filters-and-how-do-they-work) |
| `rank_scale` | string | *defines the scale used for calculating and displaying the `rank` values*<br>optional field<br>you can use this parameter to choose whether rank values are presented on a 0–100 or 0–1000 scale<br>possible values:<br>`one_hundred` — rank values are displayed on a 0–100 scale<br>`one_thousand` — rank values are displayed on a 0–1000 scale<br>default value: `one_thousand`<br>learn more about how this parameter works in [this Help Center article](https://dataforseo.com/help-center/using-the-rank_scale-parameter-in-content-analysis-api) |
| `tag` | string | *user-defined task identifier*<br>optional field<br>*the character limit is 255*<br>you can use this parameter to identify the task and match it with the result<br>you will find the specified `tag` value in the `data` object of the response |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)<br>**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total tasks cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task *<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `type` | string | *type of element = **‘content_analysis_sentiment_analysis’*** |
| `positive_connotation_distribution` | object | *citation distribution by sentiment connotation types*<br>contains objects with citation counts and relevant data distributed by types of sentiments (sentiment polarity);<br>possible sentiment connotation types: `positive`, `negative`, `neutral`<br> |
| `$positive` | object | *positive, negative, or neutral connotations*<br>variable can take the following values: `positive`, `negative`, `neutral`<br> |
| `type` | string | *type of element = **‘content_analysis_summary’*** |
| `total_count` | integer | *total number of relevant results* |
| `rank` | integer | *rank of all relevant URLs* |
| `top_domains` | array | *top relevant domains*<br>contains objects with top relevant domains and the number of citations per each domain |
| `sentiment_connotations` | object | *sentiment connotations*<br>contains relevant sentiments (emotional reactions) and the number of citations per each sentiment;<br>possible connotations: `"anger"`, `"happiness"`, `"love"`, `"sadness"`, `"share"`, `"fun"`<br> |
| `connotation_types` | object | *connotation types*<br>contains types of sentiments (sentiment polarity) related to the keyword citation and citation count per each sentiment type;<br>possible connotation types: `"positive"`, `"negative"`, `"neutral"` |
| `text_categories` | array | *text categories*<br>contains text categories and citation count in each text category<br>to obtain a full list of available categories, refer to the [Categories](https://docs.dataforseo.com/v3/content_analysis/categories/) endpoint |
| `page_categories` | array | *page categories*<br>contains objects with page categories and citation count in each page category<br>to obtain a full list of available categories, refer to the [Categories](https://docs.dataforseo.com/v3/content_analysis/categories/) endpoint |
| `page_types` | object | *page types*<br>contains page types and citation count per each page type |
| `countries` | object | *countries*<br>contains countries and citation count in each country<br>to obtain a full list of available countries, refer to the [Locations](https://docs.dataforseo.com/v3/content_analysis/locations/) endpoint |
| `languages` | object | *languages*<br>to obtain a full list of available languages, refer to the [Languages](https://docs.dataforseo.com/v3/content_analysis/languages/) endpoint |
| `sentiment_connotation_distribution` | object | *citation distribution by sentiment connotations*<br>contains objects with citation counts and relevant data distributed by sentiments (emotional reactions);<br>possible sentiment connotation types: `anger`, `happiness`, `love`, `sadness`, `share`, `fun`<br> |
| `$anger` | object | *sentiment name*<br>variable can take the following values: `anger`, `happiness`, `love`, `sadness`, `share`, `fun`<br> |
| `type` | string | *type of element = **‘content_analysis_summary’*** |
| `total_count` | integer | *total number of relevant results* |
| `rank` | integer | *rank of all relevant URLs* |
| `top_domains` | array | *top relevant domains*<br>contains objects with top relevant domains and the number of citations per each domain |
| `sentiment_connotations` | object | *sentiment connotations*<br>contains relevant sentiments (emotional reactions) and the number of citations per each sentiment;<br>possible connotations: `"anger"`, `"happiness"`, `"love"`, `"sadness"`, `"share"`, `"fun"`<br> |
| `connotation_types` | object | *connotation types*<br>contains types of sentiments (sentiment polarity) related to the keyword citation and citation count per each sentiment type;<br>possible connotation types: `"positive"`, `"negative"`, `"neutral"` |
| `text_categories` | array | *text categories*<br>contains text categories and citation count in each text category<br>to obtain a full list of available categories, refer to the [Categories](https://docs.dataforseo.com/v3/content_analysis/categories/) endpoint |
| `page_categories` | array | *page categories*<br>contains objects with page categories and citation count in each page category<br>to obtain a full list of available categories, refer to the [Categories](https://docs.dataforseo.com/v3/content_analysis/categories/) endpoint |
| `page_types` | object | *page types*<br>contains page types and citation count per each page type |
| `countries` | object | *countries*<br>contains countries and citation count in each country<br>to obtain a full list of available countries, refer to the [Locations](https://docs.dataforseo.com/v3/content_analysis/locations/) endpoint |
| `languages` | object | *languages*<br>to obtain a full list of available countries, refer to the [Languages](https://docs.dataforseo.com/v3/content_analysis/languages/) endpoint |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Rating Distribution
*Source: [https://docs.dataforseo.com/v3/content_analysis/rating_distribution/live/](https://docs.dataforseo.com/v3/content_analysis/rating_distribution/live/)*
#### Content Analysis – Rating Distribution API

This endpoint will provide you with rating distribution data for the keyword and other parameters specified in the request.

POSThttps://api.dataforseo.com/v3/content_analysis/rating_distribution/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/content-analysis-api/content-analysis) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `keyword` | string | *target keyword*<br>**required field**<br>UTF-8 encoding<br>the keywords will be converted to a lowercase format;<br>**Note**: to match an exact phrase instead of a stand-alone keyword, use double quotes and backslashes;<br>example:<br>`"keyword": "\"tesla palo alto\""`<br>learn more about rules and limitations of `keyword` and `keywords` fields in DataForSEO APIs in this [Help Center article](https://dataforseo.com/help-center/rules-and-limitations-of-keyword-and-keywords-fields-in-dataforseo-apis) |
| `keyword_fields` | object | *target keyword fields and target keywords*<br>optional field<br>use this parameter to filter the dataset by keywords that certain fields should contain;<br>fields you can specify: `title`, `main_title`, `previous_title`, `snippet`<br>you can indicate several fields;<br>**Note**: to match an exact phrase instead of a stand-alone keyword, use double quotes and backslashes;<br>example:<br>`"keyword_fields": {<br> "snippet": "\"logitech mouse\"",<br> "main_title": "sale"<br>}` |
| `page_type` | array | *target page types*<br>optional field<br>use this parameter to filter the dataset by page types<br>possible values:<br>`"ecommerce"`, `"news"`, `"blogs"`, `"message-boards"`, `"organization"`<br> |
| `internal_list_limit` | integer | *maximum number of elements within internal arrays*<br>optional field<br>you can use this field to limit the number of elements within the following arrays:<br>`top_domains`<br>`text_categories`<br>`page_categories`<br>`countries`<br>`languages`<br>default value: `1`<br>maximum value: `20` |
| `search_mode` | string | *results grouping type*<br>optional field<br>possible grouping types:<br>`as_is` – returns all citations for the target `keyword`<br>`one_per_domain` – returns one citation of the `keyword` per domain<br>default value: `as_is` |
| `positive_connotation_threshold` | float | *positive connotation threshold*<br>optional field<br>specified as the probability index threshold for positive sentiment related to the citation content<br>if you specify this field, `connotation_types` object in the response will only contain data on citations with `positive` sentiment probability more than or equal to the specified value<br>possible values: from `0` to `1`<br>default value: `0.4` |
| `sentiments_connotation_threshold` | float | *sentiment connotation threshold*<br>optional field<br>specified as the probability index threshold for sentiment connotations related to the citation content<br>if you specify this field, `sentiment_connotations` object in the response will only contain data on citations where the probability per each sentiment is more than or equal to the specified value<br>possible values: from `0` to `1`<br>default value: `0.4` |
| `initial_dataset_filters` | array | *initial dataset filtering parameters*<br>optional field<br>initial filtering parameters that apply to fields in the [Search endpoint](https://docs.dataforseo.com/v3/content_analysis/search/live/?bash)<br>**you can add several filters at once (8 filters maximum)**<br>you should set a logical operator `and`, `or` between the conditions<br>the following operators are supported:<br>`regex`, `not_regex`, `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`, `like`,`not_like`, `has`, `has_not`, `match`, `not_match`<br>you can use the `%` operator with `like` and `not_like` to match any string of zero or more characters<br>example:<br>`["domain","<>", "logitech.com"]`<br>`[["domain","<>","logitech.com"],"and",["content_info.connotation_types.negative",">",1000]]`<br>`[["domain","<>","logitech.com"]],<br>"and",<br>[["content_info.connotation_types.negative",">",1000],<br>"or",<br>["content_info.text_category","has",10994]]]`<br>for more information about filters, please refer to [Content Analysis API – Filters](https://docs.dataforseo.com/v3/content_analysis/filters)<br>learn more about the initial dataset filters in [this help center article.](https://dataforseo.com/help-center/what-are-the-initial-dataset-filters-and-how-do-they-work) |
| `rank_scale` | string | *defines the scale used for calculating and displaying the `rank` values*<br>optional field<br>you can use this parameter to choose whether rank values are presented on a 0–100 or 0–1000 scale<br>possible values:<br>`one_hundred` — rank values are displayed on a 0–100 scale<br>`one_thousand` — rank values are displayed on a 0–1000 scale<br>default value: `one_thousand`<br>learn more about how this parameter works in [this Help Center article](https://dataforseo.com/help-center/using-the-rank_scale-parameter-in-content-analysis-api) |
| `tag` | string | *user-defined task identifier*<br>optional field<br>*the character limit is 255*<br>you can use this parameter to identify the task and match it with the result<br>you will find the specified `tag` value in the `data` object of the response |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)<br>**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total tasks cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task *<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `type` | string | *type of element = **‘content_analysis_rating_distribution’*** |
| `min` | float | *min rating on a distribution scale* |
| `max` | float | *max rating on a distribution scale* |
| `metrics` | object | *contains rating distribution metrics* |
| `type` | string | *type of element = **‘content_analysis_summary’*** |
| `total_count` | integer | *total amount of results in our database relevant to your request* |
| `rank` | integer | *rank of all URLs citing the `keyword`*<br>normalized sum of ranks of all URLs citing the target `keyword` |
| `top_domains` | array | *top domains citing the target keyword*<br>contains objects with top domains citing the target keyword and citation count per each domain |
| `sentiment_connotations` | object | *sentiment connotations*<br>contains sentiments (emotional reactions) related to the target keyword citation and the number of citations per each sentiment;<br>possible connotations: `"anger"`, `"happiness"`, `"love"`, `"sadness"`, `"share"`, `"fun"`<br> |
| `connotation_types` | object | *connotation types*<br>contains types of sentiments (sentiment polarity) related to the keyword citation and citation count per each sentiment type;<br>possible connotation types: `"positive"`, `"negative"`, `"neutral"` |
| `text_categories` | array | *text categories*<br>contains objects with text categories and citation count in each text category<br>to obtain a full list of available categories, refer to the [Categories](https://docs.dataforseo.com/v3/content_analysis/categories/) endpoint |
| `page_categories` | array | *page categories*<br>contains objects with page categories and citation count in each page category<br>to obtain a full list of available categories, refer to the [Categories](https://docs.dataforseo.com/v3/content_analysis/categories/) endpoint |
| `page_types` | object | *page types*<br>contains page types and citation count per each page type |
| `countries` | object | *countries*<br>contains countries and citation count in each country<br>to obtain a full list of available countries, refer to the [Locations](https://docs.dataforseo.com/v3/content_analysis/locations/) endpoint<br> |
| `languages` | object | *languages*<br>contains languages and citation count in each language<br>to obtain a full list of available languages, refer to the [Languages](https://docs.dataforseo.com/v3/content_analysis/languages/) endpoint |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Phrase Trends
*Source: [https://docs.dataforseo.com/v3/content_analysis/phrase_trends/live/](https://docs.dataforseo.com/v3/content_analysis/phrase_trends/live/)*
#### Content Analysis – Phrase Trends API

This endpoint will provide you with data on all citations of the target keyword for the indicated date range.

Historical data is available from `2022-10-31`.

POSThttps://api.dataforseo.com/v3/content_analysis/phrase_trends/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/content-analysis-api/content-analysis) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute.

You can specify the number of results you want to retrieve, filter and sort them.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `keyword` | string | *target keyword*<br>**required field**<br>UTF-8 encoding<br>the keywords will be converted to a lowercase format;<br>**Note**: to match an exact phrase instead of a stand-alone keyword, use double quotes and backslashes;<br>example:<br>`"keyword": "\"tesla palo alto\""`<br>learn more about rules and limitations of `keyword` and `keywords` fields in DataForSEO APIs in this [Help Center article](https://dataforseo.com/help-center/rules-and-limitations-of-keyword-and-keywords-fields-in-dataforseo-apis) |
| `keyword_fields` | object | *target keyword fields and target keywords*<br>optional field<br>use this parameter to filter the dataset by keywords that certain fields should contain;<br>fields you can specify: `title`, `main_title`, `previous_title`, `snippet`<br>you can indicate several fields;<br>**Note**: to match an exact phrase instead of a stand-alone keyword, use double quotes and backslashes;<br>example:<br>`"keyword_fields": {<br> "snippet": "\"logitech mouse\"",<br> "main_title": "sale"<br>}` |
| `page_type` | array | *target page types*<br>optional field<br>use this parameter to filter the dataset by page types<br>possible values:<br>`"ecommerce"`, `"news"`, `"blogs"`, `"message-boards"`, `"organization"` |
| `search_mode` | string | *results grouping type*<br>optional field<br>possible grouping types:<br>`as_is` – returns data on all citations for the target `keyword`<br>`one_per_domain` – returns data on one citation of the `keyword` per domain<br>default value: `as_is` |
| `internal_list_limit` | integer | *maximum number of elements within internal arrays*<br>optional field<br>you can use this field to limit the number of elements within the following arrays:<br>`top_domains`<br>`text_categories`<br>`page_categories`<br>`countries`<br>`languages`<br>default value: `1`<br>maximum value: `20` |
| `date_from` | string | *starting date of the time range*<br>**required field**<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2019-01-15"` |
| `date_to` | string | *ending date of the time range*<br>optional field<br>if you don’t specify this field, today’s date will be used by default<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2019-01-15"` |
| `date_group` | string | *time range which will be used to group the results*<br>optional field<br>default value: `month`<br>possible values: `day`, `week`, `month` |
| `initial_dataset_filters` | array | *initial dataset filtering parameters*<br>optional field<br>initial filtering parameters that apply to fields in the [Search endpoint](https://docs.dataforseo.com/v3/content_analysis/search/live/?bash);<br>**you can add several filters at once (8 filters maximum);**<br>you should set a logical operator `and`, `or` between the conditions;<br>the following operators are supported:<br>`regex`, `not_regex`, `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`, `like`,`not_like`, `has`, `has_not`, `match`, `not_match`<br>you can use the `%` operator with `like` and `not_like` to match any string of zero or more characters;<br>example:<br>`["domain","<>", "logitech.com"]`<br>`[["domain","<>","logitech.com"],"and",["content_info.connotation_types.negative",">",1000]]`<br>`[["domain","<>","logitech.com"]],<br>"and",<br>[["content_info.connotation_types.negative",">",1000],<br>"or",<br>["content_info.text_category","has",10994]]]`<br>for more information about filters, please refer to [Content Analysis API – Filters](https://docs.dataforseo.com/v3/content_analysis/filters)<br>learn more about the initial dataset filters in [this help center article.](https://dataforseo.com/help-center/what-are-the-initial-dataset-filters-and-how-do-they-work) |
| `rank_scale` | string | *defines the scale used for calculating and displaying the `rank` values*<br>optional field<br>you can use this parameter to choose whether rank values are presented on a 0–100 or 0–1000 scale<br>possible values:<br>`one_hundred` — rank values are displayed on a 0–100 scale<br>`one_thousand` — rank values are displayed on a 0–1000 scale<br>default value: `one_thousand`<br>learn more about how this parameter works in [this Help Center article](https://dataforseo.com/help-center/using-the-rank_scale-parameter-in-content-analysis-api) |
| `tag` | string | *user-defined task identifier*<br>optional field<br>*the character limit is 255*<br>you can use this parameter to identify the task and match it with the result<br>you will find the specified `tag` value in the `data` object of the response |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)<br>**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total tasks cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task *<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `type` | string | *type of element = **‘content_analysis_trends’*** |
| `date` | string | *date for which the data is provided* |
| `total_count` | integer | *total number of results in our database relevant to your request* |
| `rank` | integer | *rank of all URLs citing the `keyword`*<br>normalized sum of ranks of all URLs citing the target `keyword` for the given date |
| `top_domains` | array | *top domains citing the target keyword*<br>contains objects with top domains citing the target keyword and citation count per each domain |
| `sentiment_connotations` | object | *sentiment connotations*<br>contains sentiments (emotional reactions) related to the target keyword citation and the number of citations per each sentiment<br>possible connotations: `"anger"`, `"happiness"`, `"love"`, `"sadness"`, `"share"`, `"fun"` |
| `connotation_types` | object | *connotation types*<br>contains types of sentiments (sentiment polarity) related to the keyword citation and citation count per each sentiment type<br>possible connotation types: `"positive"`, `"negative"`, `"neutral"` |
| `text_categories` | array | *text categories*<br>contains objects with text categories and citation count in each text category<br>to obtain a full list of available categories, refer to the [Categories](https://docs.dataforseo.com/v3/content_analysis/categories/) endpoint |
| `page_categories` | array | *page categories*<br>contains objects with page categories and citation count in each page category<br>to obtain a full list of available categories, refer to the [Categories](https://docs.dataforseo.com/v3/content_analysis/categories/) endpoint |
| `page_types` | object | *page types*<br>contains page types and citation count per each page type |
| `countries` | object | *countries*<br>contains countries and citation count in each country<br>to obtain a full list of available countries, refer to the [Locations](https://docs.dataforseo.com/v3/content_analysis/locations/) endpoint |
| `languages` | object | *languages*<br>contains languages and citation count in each language<br>to obtain a full list of available languages, refer to the [Languages](https://docs.dataforseo.com/v3/content_analysis/languages/) endpoint |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


### Category Trends
*Source: [https://docs.dataforseo.com/v3/content_analysis/category_trends/live/](https://docs.dataforseo.com/v3/content_analysis/category_trends/live/)*
#### Content Analysis – Category Trends API

This endpoint will provide you with data on all citations in the target category for the indicated date range.

Historical data is available from `2022-10-31`.

POSThttps://api.dataforseo.com/v3/content_analysis/category_trends/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/content-analysis-api/content-analysis) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute.

You can specify the number of results you want to retrieve, filter and sort them.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `category_code` | integer | *target category code*<br>**required field**<br>to obtain a full list of available categories, refer to the [Categories](https://docs.dataforseo.com/v3/content_analysis/categories/) endpoint |
| `page_type` | array | *target page types*<br>optional field<br>use this parameter to filter the dataset by page types<br>possible values:<br>`"ecommerce"`, `"news"`, `"blogs"`, `"message-boards"`, `"organization"` |
| `search_mode` | string | *results grouping type*<br>optional field<br>possible grouping types:<br>`as_is` – returns data on all citations for the target `category_code`<br>`one_per_domain` – returns data on one citation of the `category_code` per domain<br>default value: `as_is` |
| `internal_list_limit` | integer | *maximum number of elements within internal arrays*<br>optional field<br>you can use this field to limit the number of elements within the following arrays:<br>`top_domains`<br>`text_categories`<br>`page_categories`<br>`countries`<br>`languages`<br>default value: `1`<br>maximum value: `20` |
| `date_from` | string | *starting date of the time range*<br>**required field**<br>minimum value: `2022-10-31`<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2019-01-15"` |
| `date_to` | string | *ending date of the time range*<br>optional field<br>if you don’t specify this field, today’s date will be used by default<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2019-01-15"` |
| `date_group` | string | *time range which will be used to group the results*<br>optional field<br>default value: `month`<br>possible values: `day`, `week`, `month` |
| `initial_dataset_filters` | array | *initial dataset filtering parameters*<br>optional field<br>initial filtering parameters that apply to fields in the [Search endpoint](https://docs.dataforseo.com/v3/content_analysis/search/live/?bash);<br>**you can add several filters at once (8 filters maximum)**<br>you should set a logical operator `and`, `or` between the conditions<br>the following operators are supported:<br>`regex`, `not_regex`, `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`, `like`,`not_like`, `has`, `has_not`, `match`, `not_match`<br>you can use the `%` operator with `like` and `not_like` to match any string of zero or more characters<br>example:<br>`["domain","<>", "logitech.com"]`<br>`[["domain","<>","logitech.com"],"and",["content_info.connotation_types.negative",">",1000]]`<br>`[["domain","<>","logitech.com"]],<br>"and",<br>[["content_info.connotation_types.negative",">",1000],<br>"or",<br>["content_info.text_category","has",10994]]]`<br>for more information about filters, please refer to [Content Analysis API – Filters](https://docs.dataforseo.com/v3/content_analysis/filters)<br>learn more about the initial dataset filters in [this help center article.](https://dataforseo.com/help-center/what-are-the-initial-dataset-filters-and-how-do-they-work) |
| `rank_scale` | string | *defines the scale used for calculating and displaying the `rank` values*<br>optional field<br>you can use this parameter to choose whether rank values are presented on a 0–100 or 0–1000 scale<br>possible values:<br>`one_hundred` — rank values are displayed on a 0–100 scale<br>`one_thousand` — rank values are displayed on a 0–1000 scale<br>default value: `one_thousand`<br>learn more about how this parameter works in [this Help Center article](https://dataforseo.com/help-center/using-the-rank_scale-parameter-in-content-analysis-api) |
| `tag` | string | *user-defined task identifier*<br>optional field<br>*the character limit is 255*<br>you can use this parameter to identify the task and match it with the result<br>you will find the specified `tag` value in the `data` object of the response |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)<br>**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total tasks cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task *<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `type` | string | *type of element = **‘content_analysis_trends’*** |
| `date` | string | *date for which the data is provided* |
| `total_count` | integer | *total number of results in our database relevant to your request* |
| `rank` | integer | *rank of all URLs citing the `keyword`*<br>normalized sum of ranks of all URLs citing the target `keyword` for the given date |
| `top_domains` | array | *top domains citing the target keyword*<br>contains objects with top domains citing the target category and citation count per each domain |
| `sentiment_connotations` | object | *sentiment connotations*<br>contains sentiments (emotional reactions) related to the target category citation and the number of citations per each sentiment<br>possible connotations: `"anger"`, `"fear"`, `"happiness"`, `"love"`, `"sadness"`, `"share"`, `"neutral"`, `"fun"` |
| `connotation_types` | object | *connotation types*<br>contains types of sentiments (sentiment polarity) related to the category citation and citation count per each sentiment type<br>possible connotation types: `"positive"`, `"negative"`, `"neutral"` |
| `text_categories` | array | *text categories*<br>contains objects with text categories and citation count in each text category<br>to obtain a full list of available categories, refer to the [Categories](https://docs.dataforseo.com/v3/content_analysis/categories/) endpoint |
| `page_categories` | array | *page categories*<br>contains objects with page categories and citation count in each page category<br>to obtain a full list of available categories, refer to the [Categories](https://docs.dataforseo.com/v3/content_analysis/categories/) endpoint |
| `page_types` | object | *page types*<br>contains page types and citation count per each page type |
| `countries` | object | *countries*<br>contains countries and citation count in each country<br>to obtain a full list of available countries, refer to the [Locations](https://docs.dataforseo.com/v3/content_analysis/locations/) endpoint |
| `languages` | object | *languages*<br>contains languages and citation count in each language<br>to obtain a full list of available languages, refer to the [Languages](https://docs.dataforseo.com/v3/content_analysis/languages/) endpoint |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---
