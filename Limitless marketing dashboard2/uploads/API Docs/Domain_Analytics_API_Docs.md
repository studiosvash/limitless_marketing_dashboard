# Domain Analytics API Documentation
*Consolidated main text documentation of Domain Analytics API compiled from docs.dataforseo.com*

---


### Overview
*Source: [https://docs.dataforseo.com/v3/domain_analytics/overview/](https://docs.dataforseo.com/v3/domain_analytics/overview/)*
### Domain Analytics API: Overview

This API provides data on website traffic, technologies, and Whois details

**Domain Analytics API** is a comprehensive source of data for analyzing websites, competitors, and markets.

It encompasses a broad range of endpoints grouped by their analytical scope:

**• [Domain Analytics Technologies API](https://docs.dataforseo.com/v3/domain_analytics/technologies/overview/)** helps identify all possible technologies used for building websites. It allows reviewing stats by domain and by technology name, category or group.

**• [Domain Analytics Whois API](https://docs.dataforseo.com/v3/domain_analytics/whois/overview/)** offers Whois data enriched with backlink stats, and ranking and traffic info from organic and paid search results.
 
To find answers to common questions about Domain Analytics API and find guidance on the efficient use of its features, [visit our Help Center.](https://dataforseo.com/help-center/category/domain-analytics-api)

##### Methods

Domain Analytics Whois API and Domain Analytics Technologies API support only the Live method of data retrieval. It doesn’t require making separate POST and GET requests to the corresponding endpoints and delivers instant results.

You can send up to 2000 API calls per minute. Contact us if you would like to raise the limit. Note that the maximum number of Live requests that can be sent simultaneously is limited to 30.

##### Cost

The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/domain-analytics-api/) page.

You can check your spending in your [account dashboard](https://app.dataforseo.com/api-access) or by making a separate call to [the User Data endpoint](https://docs.dataforseo.com/v3/appendix/user_data/?php).

---


#### Overview
*Source: [https://docs.dataforseo.com/v3/domain_analytics/technologies/overview/](https://docs.dataforseo.com/v3/domain_analytics/technologies/overview/)*
### Domain Analytics Technologies API: Overview

This API provides data on technologies used by various websites across the Internet

Domain Analytics Technologies API will help you identify all possible technologies used for building websites. It allows reviewing stats by domain and by technology name, category or group.

[See the full list of available technologies.](https://docs.dataforseo.com/v3/domain_analytics/technologies/technologies/) It is structured by groups and categories each particular technology belongs to.

Domain Analytics Technologies API encompasses a range of mission-tailored endpoints:

• [Aggregation Technologies](https://docs.dataforseo.com/v3/domain_analytics/technologies/aggregation_technologies/live/) will furnish you with a list of the most popular technologies websites use alongside the technologies you specify.
• [Technologies Summary](https://docs.dataforseo.com/v3/domain_analytics/technologies/technologies_summary/live/) will give you data on the number of domains across different countries and languages that use the specified technologies.
• [Technology Stats](https://docs.dataforseo.com/v3/domain_analytics/technologies/technology_stats/live/) will surface historical data on the number of domains across different countries and languages that use the specified technology.
• [Domains by Technology](https://docs.dataforseo.com/v3/domain_analytics/technologies/domains_by_technology/live/) will provide you with domains based on the technologies they use.
• [Domains by HTML Terms](https://docs.dataforseo.com/v3/domain_analytics/technologies/domains_by_html_terms/live/) will serve you with domains based on the HTML terms their homepage contains.
• [Domain Technologies](https://docs.dataforseo.com/v3/domain_analytics/technologies/domain_technologies/live/) will supply you with a list of technologies used by a particular domain.

Domain Analytics Technologies API allows applying custom filtration to the dataset that will be retrieved. By using filters, you can effortlessly get exactly the data you need. For more information, please refer to the [Filters for Domain Analytics Technologies API.](https://docs.dataforseo.com/v3/domain_analytics/technologies/filters/)

To find answers on common questions about Domain Analytics Technologies API and find guidance on efficient use of its features, [visit our Help Center.](https://dataforseo.com/help-center/category/domain-analytics-api)

##### Methods

Domain Analytics Technologies API supports only the Live method of data retrieval. It doesn’t require making separate POST and GET requests to the corresponding endpoints and delivers instant results.

You can send up to 2000 API calls per minute. Contact us if you would like to raise the limit.

##### Cost

The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/domain-analytics-api/domain-technologies-api) page.

You can check your spending in your [account dashboard](https://app.dataforseo.com/api-access) or by making a separate call to [the User Data endpoint](https://docs.dataforseo.com/v3/appendix/user_data/?php).

---


#### Filters
*Source: [https://docs.dataforseo.com/v3/domain_analytics/technologies/filters/](https://docs.dataforseo.com/v3/domain_analytics/technologies/filters/)*
#### Filters for Domain Analytics Technologies API

Here you will find all the necessary information about filters that can be used with Domain Analytics Technologies API endpoints.

Note that filters are associated with a certain object in the `result` array, and should be specified accordingly.

Pricing

Your account will not be charged for using this API

GEThttps://api.dataforseo.com/v3/domain_analytics/technologies/available_filters

You will receive the full list of filters by calling this API. You can also download the full list of possible filters [by this link.](https://cdn.dataforseo.com/v3/available_filters.php?api=domain_analytics/technologies)

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

Below you will find a detailed description of the structure that should be used to specify filters for Domain Analytics Technologies API.

**Description of the fields:**

| Field name | Type | Description |
| --- | --- | --- |
| `filters` | array | *array of results filtering parameters*<br>filters have the following structure:<br>**[`filered_field`, `filter_operator`, `filter_value`]**<br>**you can add several filters at once (8 filters maximum)**<br>if you add more than one filter, you must set a logical operator `and`, `or` between the conditions<br>example:<br>`[["domain_rank",">",800],"and",["country_iso_code","=","US"]]` |
| `filtered_field` | str | *fields that support filtration*<br>you can use the following fields to filter the results: `domain_rank`, `last_visited`, `country_iso_code`, `language_code`, `content_language_code`<br>see **[available filters](#dtfiltres)** for more information |
| `filter_operator` | str | *operator in the filter*<br>available filter operators:<br>• if **`num`**: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>• if **`str`**: `like`, `not_like`, `=`, `<>`, `regex`, `not_regex`<br>• if **`time`**: `<`, `>`<br>note: `time` should be specified in the format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2021-01-29 15:02:37 +00:00`<br>if you specify `in` or `not_in` operator, the `$filter_value` should be specified as an array<br>example:<br>`["domain_rank","in",[100,500]]`<br>the `regex` and `not_regex` operators can be specified with `string` values using the [RE2 regex](https://github.com/google/re2/wiki/Syntax) syntax; |
| `filter_value` | | *filtering value*<br>values specified in the `filter_value` should match the format of the specified `filtered_field` |
| **[available filters]()** | | |
| `domain_rank` | num | *backlink rank of the domain*<br>the following operators are supported: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>example:<br>`"filters": ["domain_rank","in",[100,500]]` |
| `domain` | str | *domain name*<br>**note:** this filter is supported in the [Domains by HTML Terms endpoint](https://docs.dataforseo.com/v3/domain_analytics/technologies/domains_by_html_terms/live/) only<br>the following operators are supported: `=`, `<>`, `like`, `not_like`<br>you can use the `%` operator with `like` and `not_like` to match any string of zero or more characters<br>example:<br>`["domain","like","%seo%"]` |
| `last_visited` | time | *most recent date when our crawler visited the domain*<br>the following operators are supported: `<`, `>`<br>note: `last_visited` should be specified in the format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`"filters": ["last_visited",">","2022-09-29 15:02:37 +00:00"]` |
| `country_iso_code` | str | *domain ISO code*<br>the following operators are supported: `=`, `<>`, `like`, `not_like`<br>example:<br>`"filters": ["country_iso_code","=","US"]` |
| `language_code` | str | *domain language*<br>the following operators are supported: `=`, `<>`, `like`, `not_like`<br>example:<br>`"filters": ["language_code","=","en"]` |
| `content_language_code` | str | *content language*<br>the following operators are supported: `=`, `<>`, `like`, `not_like`<br>example:<br>`"filters": ["content_language_code","<>","en"]` |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The list of available filtration parameters:

---


#### Locations
*Source: [https://docs.dataforseo.com/v3/domain_analytics/technologies/locations/](https://docs.dataforseo.com/v3/domain_analytics/technologies/locations/)*
#### List of Locations for Domain Analytics Technologies API

Pricing

Your account will not be charged for using this API

GEThttps://api.dataforseo.com/v3/domain_analytics/technologies/locations

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


#### Languages
*Source: [https://docs.dataforseo.com/v3/domain_analytics/technologies/languages/](https://docs.dataforseo.com/v3/domain_analytics/technologies/languages/)*
#### List of Languages for Domain Analytics Technologies API

Pricing

Your account will not be charged for using this API

GEThttps://api.dataforseo.com/v3/domain_analytics/technologies/languages

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


#### Technologies
*Source: [https://docs.dataforseo.com/v3/domain_analytics/technologies/technologies/](https://docs.dataforseo.com/v3/domain_analytics/technologies/technologies/)*
#### List of Technologies for Domain Analytics Technologies API

This endpoint will provide you with the full list of available technologies structured by technology groups and categories each particular technology belongs to.

GEThttps://api.dataforseo.com/v3/domain_analytics/technologies/technologies

Pricing

Your account will not be charged for using this API

By calling this API you will receive the list of technologies supported by Domain Analytics Technologies API.
As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information about available technologies.

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
| `groups` | array | *array of technology groups* |
| `id` | string | *id of the technology group*<br>example:<br>`marketing`, `sales` |
| `title` | string | *title of the technology group* |
| `categories` | array | *technology categories in this group* |
| `id` | string | *id of the technology category*<br>example:<br>`crm`, `cart_abandonment` |
| `path` | string | *path to the technology category*<br>example:<br>`user_generated_content.content_curation` |
| `title` | string | *title of the technology category* |
| `technologies` | array | *list of technologies in this category*<br>example:<br>`"Salesforce"`, `"CareCart"` |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


#### Aggregation Technologies
*Source: [https://docs.dataforseo.com/v3/domain_analytics/technologies/aggregation_technologies/live/](https://docs.dataforseo.com/v3/domain_analytics/technologies/aggregation_technologies/live/)*
#### Aggregation Technologies

The Aggregation Technologies endpoint will provide you with a list of the most popular technologies websites use alongside the technologies you specify. Alternatively, you can specify technology categories or groups to obtain wider stats.

POSThttps://api.dataforseo.com/v3/domain_analytics/technologies/aggregation_technologies/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/domain-analytics-api/domain-technologies-api) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API requests per minute.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `group` | string | *id of the target technology group*<br>**required field if you don’t specify `technology`, `category` or `keyword`**<br>at least one field (`group`, `category`, `keyword`, `technology`) must be set<br>you can find the full list of technology group ids [on this page](https://docs.dataforseo.com/v3/domain_analytics/technologies/technologies)<br>example:<br>`"marketing"` |
| `category` | string | *id of the target technology category*<br>**required field if you don’t specify `group`, `keyword` or `technology`**<br>at least one field (`group`, `category`, `keyword`, `technology`) must be set<br>you can find the full list of technology category ids [on this page](https://docs.dataforseo.com/v3/domain_analytics/technologies/technologies)<br>example:<br>`"crm"` |
| `technology` | string | *target technology*<br>**required field if you don’t specify `group`, `keyword` or `category`**<br>at least one field (`group`, `category`, `keyword`, `technology`) must be set<br>you can find the full list of technologies [on this page](https://docs.dataforseo.com/v3/domain_analytics/technologies/technologies)<br>example:<br>`"Salesforce"` |
| `keyword` | string | *target keyword in the domain’s meta keywords*<br>**required field if you don’t specify `group`, `category` or `technology`**<br>at least one field (`group`, `category`, `keyword`, `technology`) must be set<br>UTF-8 encoding<br>example:<br>`"seo"`learn more about rules and limitations of `keyword` and `keywords` fields in DataForSEO APIs in this [Help Center article](https://dataforseo.com/help-center/rules-and-limitations-of-keyword-and-keywords-fields-in-dataforseo-apis) |
| `mode` | string | *search mode*<br>optional field<br>possible search mode types:<br>`as_is` – search for results exactly matching the specified group ids, category ids, or technology names<br>`entry` – search for results matching a part of the specified group ids, category ids, or technology names<br>default value: `as_is` |
| `filters` | array | *array of results filtering parameters*<br>optional field<br>**you can add several filters at once (8 filters maximum)**<br>you should set a logical operator `and`, `or` between the conditions<br>the following operators are supported:<br>`<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`, `like`,`not_like`<br>you can use the `%` operator with `like` and `not_like` to match any string of zero or more characters<br>you can use the following parameters to filter the results: `domain_rank`, `last_visited`, `country_iso_code`, `language_code`, `content_language_code`<br>**Note:** all filtering parameters are taken from the `domain_technology_item` of the [domain_technologies](https://docs.dataforseo.com/v3/domain_analytics/technologies/filters) endpoint;<br>example:<br>`[["country_iso_code","=","US"],<br>"and",<br>["domain_rank",">",800]]`for more information about filters, please refer to [Domain Analytics Technologies API – Filters](https://docs.dataforseo.com/v3/domain_analytics/technologies/filters) |
| `order_by` | array | *results sorting rules*<br>optional field<br>you can use the following values to sort the results: `groups_count`, `categories_count`, `technologies_count`<br>possible sorting types:<br>`asc` – results will be sorted in the ascending order<br>`desc` – results will be sorted in the descending order<br>you should use a comma to set up a sorting type<br>example:<br>`["groups_count,desc"]`<br>**note that you can set no more than three sorting rules in a single request**<br>you should use a comma to separate several sorting rules<br>example:<br>`["groups_count,desc","technologies_count,desc"]`<br>default value:<br>`["groups_count,desc","categories_count,desc","technologies_count,desc"]` |
| `internal_groups_list_limit` | integer | *maximum number of returned technology groups*<br>optional field<br>you can use this field to limit the number of items with identical `"group"` in the results<br>default value: `5`<br>minimum value: `1`<br>maximum value: `10000` |
| `internal_categories_list_limit` | integer | *maximum number of returned technology categories within the same group*<br>optional field<br>you can use this field to limit the number of items with identical `"category"` in the results<br>default value: `5`<br>minimum value: `1`<br>maximum value: `10000` |
| `internal_technologies_list_limit` | integer | *maximum number of returned technologies within the same category*<br>optional field<br>you can use this field to limit the number of items with identical `"technology"` in the results<br>default value: `10`<br>minimum value: `1`<br>maximum value: `10000` |
| `internal_list_limit` | integer | *maximum number of items with identical `"category"`, `"group"`, and `"technology"`*<br>optional field<br>if you use this field, the values specified in `internal_groups_list_limit`, `internal_categories_list_limit` and `internal_technologies_list_limit` will be ignored;<br>you can use this field to limit the number of items with identical `"category"`, `"group"`, or `"technology"`<br>default value: `10`<br>minimum value: `1`<br>maximum value: `10000` |
| `limit` | integer | *the maximum number of returned technologies*<br>optional field<br>default value: `100`<br>maximum value: `10000` |
| `offset` | integer | *offset in the results array of returned domains*<br>optional field<br>default value: `0`<br>maximum value: `9999`<br>if you specify the `10` value, the first ten technologies in the results array will be omitted and the data will be provided for the successive technologies |
| `tag` | string | *user-defined task identifier*<br>optional field<br>*the character limit is 255*<br>you can use this parameter to identify the task and match it with the result<br>you will find the specified `tag` value in the `data` object of the response |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)<br>**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total *tasks* cost, USD* |
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
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `total_count` | integer | *total amount of results in our database relevant to your request* |
| `items_count` | integer | *the number of results returned in the `items` array* |
| ````**type** | string | *type of element = **‘aggregation_technologies_item’*** |
| `group` | string | *technology group id* |
| `category` | string | *technology category id* |
| `technology` | string | *technology name* |
| `groups_count` | integer | *technology groups count*<br>number of domains that match the parameters you specified and are using technologies from the indicated `group` |
| `categories_count` | integer | *technology categories count*<br>number of domains that match the parameters you specified and are using technologies from the indicated `category` |
| `technologies_count` | integer | *technologies count*<br>number of domains that match the parameters you specified and are using the indicated `technology` |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


#### Technologies Summary
*Source: [https://docs.dataforseo.com/v3/domain_analytics/technologies/technologies_summary/live/](https://docs.dataforseo.com/v3/domain_analytics/technologies/technologies_summary/live/)*
#### Technologies Summary

The Technologies Summary endpoint will provide you with the number of domains across different countries and languages that use the specified technology names, technology groups, or technology categories.

POSThttps://api.dataforseo.com/v3/domain_analytics/technologies/technologies_summary/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/domain-analytics-api/domain-technologies-api) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API requests per minute.
 
**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `technology_paths` | array | *target technology paths*<br>**required field if you don’t specify `groups`, `technologies` and `categories`**<br>each technology path should be specified as a separate object containing “path” and “name”, where “path” is specified as “$group_id.$category_id” and “name” – as the name of the target technology;<br>each object with a technology path should be separated with a comma<br>you can find the full list of technology group ids, category ids and technology names [on this page](https://docs.dataforseo.com/v3/domain_analytics/technologies/technologies)<br>**note:** you can specify up to 10 technology paths in this array<br>example:<br>`[{"path": "content.cms","name": "wordpress"}, {"path": "marketing.crm","name": "salesforce"}]` |
| `groups` | array | *ids of the target technology groups*<br>**required field if you don’t specify `technologies`, `technology_paths`, `categories`, or `keywords`**<br>you can find the full list of technology group ids [on this page](https://docs.dataforseo.com/v3/domain_analytics/technologies/technologies)<br>**note:** you can specify up to 10 technology groups in this array<br>example:<br>`["sales", "marketing"]` |
| `categories` | array | *ids of the target technology categories*<br>**required field if you don’t specify `groups`, `technology_paths`, `technologies`, or `keywords`**<br>you can find the full list of technology category ids [on this page](https://docs.dataforseo.com/v3/domain_analytics/technologies/technologies)<br>**note:** you can specify up to 10 technology categories in this array<br>example:<br>`["payment_processors","crm"]` |
| `technologies` | array | *target technologies*<br>**required field if you don’t specify `groups`, `technology_paths`, `categories`, or `keywords`**<br>you can find the full list of technologies you can specify here [on this page](https://docs.dataforseo.com/v3/domain_analytics/technologies/technologies)<br>**note:** you can specify up to 10 technologies in this array<br>example:<br>`["Google Pay","Salesforce"]` |
| `keywords` | array | *target keywords in the domain’s title, description or meta keywords*<br>**required field if you don’t specify `groups`, `technology_paths`, `categories`, or `technologies`**<br>you can specify the maximum of 10 keywords;<br>UTF-8 encoding;<br>example:<br>`["seo","software"]`<br>learn more about rules and limitations of `keyword` and `keywords` fields in DataForSEO APIs in this [Help Center article](https://dataforseo.com/help-center/rules-and-limitations-of-keyword-and-keywords-fields-in-dataforseo-apis) |
| `mode` | string | *search mode*<br>optional field<br>possible search mode types:<br>`as_is` – search for results exactly matching the specified group ids, category ids, or technology names<br>`entry` – search for results matching a part of the specified group ids, category ids, or technology names<br>default value: `as_is` |
| `filters` | array | *array of results filtering parameters*<br>optional field<br>**you can add several filters at once (8 filters maximum)**<br>you should set a logical operator `and`, `or` between the conditions<br>the following operators are supported:<br>`<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`, `like`,`not_like`<br>you can use the `%` operator with `like` and `not_like` to match any string of zero or more characters<br>you can use the following parameters to filter the results: `domain_rank`, `last_visited`, `country_iso_code`, `language_code`, `content_language_code`<br>example:<br>`[["country_iso_code","=","US"],<br>"and",<br>["domain_rank",">",800]]`<br>for more information about filters, please refer to [Domain Analytics Technologies API – Filters](https://docs.dataforseo.com/v3/domain_analytics/technologies/filters) |
| `internal_list_limit` | integer | *maximum number of elements within internal arrays*<br>optional field<br>you can use this field to limit the number of elements within the following arrays:<br>`countries`, `languages`, `content_languages`, `keywords`<br>default value: `10`<br>minimum value: `1`<br>maximum value: `10000` |
| `tag` | string | *user-defined task identifier*<br>optional field<br>*the character limit is 255*<br>you can use this parameter to identify the task and match it with the result<br>you will find the specified `tag` value in the `data` object of the response |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)<br>**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total *tasks* cost, USD* |
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
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `countries` | object | *distribution of websites by country*<br>contains country codes and number of websites per country |
| `languages` | object | *distribution of websites by language*<br>contains language codes and number of websites per language |
| `content_languages` | object | *distribution of websites by content language*<br>contains content language codes and number of websites per language |
| `keywords` | object | *distribution of websites by keywords*<br>contains keywords found in the websites’ titles, descriptions or meta keywords, and number of websites using each keyword |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


#### Technology Stats
*Source: [https://docs.dataforseo.com/v3/domain_analytics/technologies/technology_stats/live/](https://docs.dataforseo.com/v3/domain_analytics/technologies/technology_stats/live/)*
#### Technology Stats

The Technology Stats endpoint will provide you with historical data on the number of domains across different countries and languages that use the specified technology.

Historical data is available from `2022-10-31`.

POSThttps://api.dataforseo.com/v3/domain_analytics/technologies/technology_stats/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/domain-analytics-api/domain-technologies-api) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API requests per minute.
 
**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `technology` | string | *target technology*<br>**required field**<br>you can find the full list of technologies you can specify here [on this page](https://docs.dataforseo.com/v3/domain_analytics/technologies/technologies)<br>example:<br>`"Salesforce"` |
| `date_from` | string | *starting date of the time range*<br>optional field<br>minimum value: `2022-10-31`<br>if you don’t specify this field, the minimum value will be used by default<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2023-06-01"` |
| `date_to` | string | *ending date of the time range*<br>optional field<br>if you don’t specify this field, the today’s date will be used by default<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2023-01-15"` |
| `tag` | string | *user-defined task identifier*<br>optional field<br>*the character limit is 255*<br>you can use this parameter to identify the task and match it with the result<br>you will find the specified `tag` value in the `data` object of the response |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)<br>**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total *tasks* cost, USD* |
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
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `technology` | string | *target technology* |
| `date_from` | string | *starting date of the time range* |
| `date_to` | string | *ending date of the time range* |
| `items_count` | integer | *number of items in the results array* |
| `**items**` | array | *items array* |
| `type` | string | *type of the item = **‘technology_stats_item’*** |
| `date` | string | *date for which the data is provided* |
| `domains_count` | integer | *number of domains that use the specified technology* |
| `countries` | object | *distribution of websites by country*<br>contains country codes and number of websites per country |
| `languages` | object | *distribution of websites by language*<br>contains language codes and number of websites per language |
| `domains_rank` | object | *distribution of websites by backlink rank*<br>contains domain rank ranges and number of websites per range<br>learn more about rank and how it is calculated in [this help center article](https://dataforseo.com/help-center/what_is_rank_in_backlinks_api) |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


#### Domains by Technology
*Source: [https://docs.dataforseo.com/v3/domain_analytics/technologies/domains_by_technology/live/](https://docs.dataforseo.com/v3/domain_analytics/technologies/domains_by_technology/live/)*
#### Domains by Technology

This endpoint provides domains based on the technology they use. In addition to the list of domains, you will also get their technology profiles, the country and language they belong to, and other related data.

POSThttps://api.dataforseo.com/v3/domain_analytics/technologies/domains_by_technology/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/domain-analytics-api/domain-technologies-api) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API requests per minute.

You can specify the number of results you want to retrieve, filter and sort them.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `technology_paths` | array | *target technology paths*<br>**required field if you don’t specify `groups`, `technologies`, `keywords` or `categories`**<br>at least one field (`technology_paths`, `groups`, `technologies`, `keywords` or `categories`) must be set;<br>each technology path should be specified as a separate object containing “path” and “name”, where “path” is specified as “$group_id.$category_id” and “name” – as the name of the target technology;<br>each object with a technology path should be separated with a comma<br>you can find the full list of technology group ids, category ids and technology names [on this page](https://docs.dataforseo.com/v3/domain_analytics/technologies/technologies)<br>**note:** you can specify up to 10 technology paths in this array<br>example:<br>`[{"path": "content.cms","name": "wordpress"}, {"path": "marketing.crm","name": "salesforce"}]` |
| `groups` | array | *ids of the target technology groups*<br>**required field if you don’t specify `technologies`, `technology_paths`, `keywords` or `categories`**<br>you can find the full list of technology group ids [on this page](https://docs.dataforseo.com/v3/domain_analytics/technologies/technologies)<br>**note:** you can specify up to 10 technology groups in this array<br>example:<br>`["sales", "marketing"]` |
| `categories` | array | *ids of the target technology categories*<br>**required field if you don’t specify `groups`, `technology_paths`, `keywords` or `technologies`**<br>you can find the full list of technology category ids [on this page](https://docs.dataforseo.com/v3/domain_analytics/technologies/technologies)<br>**note:** you can specify up to 10 technology categories in this array<br>example:<br>`["payment_processors","crm"]` |
| `technologies` | array | *target technologies*<br>**required field if you don’t specify `groups`, `technology_paths`, `keywords` or `categories`**<br>you can find the full list of technologies you can specify here [on this page](https://docs.dataforseo.com/v3/domain_analytics/technologies/technologies)<br>**note:** you can specify up to 10 technologies in this array<br>example:<br>`["Google Pay","Salesforce"]` |
| `keywords` | array | *target keywords in the domain’s title, description or meta keywords*<br>**required field if you don’t specify `groups`, `technology_paths`, `technologies` or `categories`**<br>optional field<br>you can specify the maximum of 10 keywords;<br>UTF-8 encoding;<br>example:<br>`["seo","software"]`<br>learn more about rules and limitations of `keyword` and `keywords` fields in DataForSEO APIs in this [Help Center article](https://dataforseo.com/help-center/rules-and-limitations-of-keyword-and-keywords-fields-in-dataforseo-apis) |
| `mode` | string | *search mode*<br>optional field<br>possible search mode types:<br>`as_is` – search for results exactly matching the specified group ids, category ids, or technology names<br>`entry` – search for results matching a part of the specified group ids, category ids, or technology names<br>default value: `as_is` |
| `filters` | array | *array of results filtering parameters*<br>optional field<br>**you can add several filters at once (8 filters maximum)**<br>you should set a logical operator `and`, `or` between the conditions<br>the following operators are supported:<br>`<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`, `like`, `not_like`<br>you can use the `%` operator with `like` and `not_like` to match any string of zero or more characters<br>example:<br>`["country_iso_code","=","US"]`<br>`[["country_iso_code","=","US"],<br>"and",<br>["domain_rank",">",100]]`<br>`[["domain_rank",">",100],<br>"and",<br>[["country_iso_code","=","US"],"or",["country_iso_code","=","CA"]]]`<br>for more information about filters, please refer to [Domain Analytics Technologies API – Filters](https://docs.dataforseo.com/v3/domain_analytics/technologies/filters) |
| `order_by` | array | *results sorting rules*<br>optional field<br>available fields:<br>`domain_rank`, `domain`, `last_visited`, `country_iso_code`, `language_code`, `content_language_code`<br>possible sorting types:<br>`asc` – results will be sorted in the ascending order<br>`desc` – results will be sorted in the descending order<br>you should use a comma to set up a sorting type<br>example:<br>`["last_visited,desc"]`<br>default rule:<br>`["domain_rank,desc"]`<br>**note that you can set no more than three sorting rules in a single request**<br>you should use a comma to separate several sorting rules<br>example:<br>`["last_visited,desc","domain_rank,desc"]` |
| `limit` | integer | *the maximum number of returned domains*<br>optional field<br>default value: `100`<br>maximum value: `10000` |
| `offset` | integer | *offset in the results array of returned domains*<br>optional field<br>default value: `0`<br>if you specify the `10` value, the first ten domains in the results array will be omitted and the data will be provided for the successive domains;<br>**Note:** the maximum value is `9999`, the sum of `limit` and `offset` must not exceed `10000`;<br>use the `offset_token` if you would like to offset more results |
| `offset_token` | string | *token for subsequent requests*<br>optional field<br>provided in the identical filed of the response to each request;<br>use this parameter to avoid timeouts while trying to obtain over 100,000 results in a single request;<br>by specifying the unique `offset_token` value from the response array, you will get the subsequent results of the initial task;<br>`offset_token` values are unique for each subsequent task<br>**Note:** if the `offset_token` is specified in the request, all other parameters should be identical to the previous request<br>learn more about this parameter on our [Help Center](https://dataforseo.com/help-center/what-is-the-difference-between-the-offset-and-offset_token-parameters#offset_token) |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)<br>**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total *tasks* cost, USD* |
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
| `data` | object | *contains the same parameters that you specified in the POST request<br>* |
| ** `result`** | array | *array of results* |
| `total_count` | integer | *total number of relevant items in the database* |
| `items_count` | integer | *number of items in the results array* |
| `offset` | integer | *specified offset value* |
| `offset_token` | string | *token for subsequent requests*<br>by specifying the unique `offset_token` when setting a new task, you will get the subsequent results of the initial task;<br>`offset_token` values are unique for each subsequent task |
| `items` | array | *items array* |
| `type` | string | *type of the item = **‘domain_technology_item’*** |
| `domain` | string | *specified domain name*<br> |
| `title` | string | *domain meta title* |
| `description` | string | *domain meta description* |
| `meta_keywords` | array | *domain meta keywords* |
| `domain_rank` | string | *backlink rank of the target domain*<br>learn more about the metric and how it is calculated in [this help center article](https://dataforseo.com/help-center/what_is_rank_in_backlinks_api) |
| `last_visited` | string | *most recent date when our crawler visited the domain*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2022-10-10 12:57:46 +00:00` |
| `country_iso_code` | string | *domain ISO code*<br>ISO code of the country that target domain is determined to belong to |
| `language_code` | string | *domain language*<br>code of the language that target domain is determined to be associated with |
| `content_language_code` | string | *content language*<br>code of the language that content on the target domain is written with |
| `phone_numbers` | array | *phone numbers of the target*<br>contact phone numbers indicated on the target website |
| `emails` | array | *emails of the target*<br>emails indicated on the target website |
| `social_graph_urls` | array | *social media links and handles*<br>social media URLs detected in the social graphs of the target website |
| `technologies` | object | *technologies used by target domain*<br>contains objects with the names of technologies used on the website;<br>to get a full list of technologies and their structure, refer to the [technologies endpoint](https://docs.dataforseo.com/v3/domain_analytics/technologies/technologies/)<br> |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


#### Domains by HTML Terms
*Source: [https://docs.dataforseo.com/v3/domain_analytics/technologies/domains_by_html_terms/live/](https://docs.dataforseo.com/v3/domain_analytics/technologies/domains_by_html_terms/live/)*
#### Domains by HTML Terms

This endpoint provides domains based on the HTML terms they use on their homepage. In addition to the list of domains, you will also get their technology profiles, the country and language they belong to, and other related data.

POSThttps://api.dataforseo.com/v3/domain_analytics/technologies/domains_by_html_terms/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/domain-analytics-api/domain-technologies-api) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API requests per minute.

You can specify the number of results you want to retrieve, filter and sort them.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `search_terms` | array | *target search terms*<br>**required field**<br>specify target HTML elements, tags, attributes, their content or all of the above<br>if you specify more than one search term, you will receive only the domains containing all of the specified terms in the HTML code of their homepage<br>maximum number of search terms you can specify: 10<br>example:<br>`["data-attrid"]` |
| `keywords` | array | *target keywords in the domain’s title, description or meta keywords*<br>optional field<br>UTF-8 encoding<br>maximum number of keywords you can specify: 10<br>example:<br>`["seo","software"]`<br>learn more about rules and limitations of `keyword` and `keywords` fields in DataForSEO APIs in this [Help Center article](https://dataforseo.com/help-center/rules-and-limitations-of-keyword-and-keywords-fields-in-dataforseo-apis) |
| `mode` | string | *search mode*<br>optional field<br>possible search mode types:<br>`strict_entry` – search for results exactly matching the order, intervals and separators in the specified search terms<br>`entry` – search for results ignoring the order, intervals and separators in the specified search terms<br>default value: `entry` |
| `filters` | array | *array of results filtering parameters*<br>optional field<br>**you can add several filters at once (8 filters maximum)**<br>you should set a logical operator `and`, `or` between the conditions<br>the following operators are supported:<br>`<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`, `like`, `not_like`<br>you can use the `%` operator with `like` and `not_like` to match any string of zero or more characters<br>example:<br>`["domain","like","%seo%"]`<br>`[["country_iso_code","=","US"],<br>"and",<br>["domain_rank",">",100]]`<br>`[["domain_rank",">",100],<br>"and",<br>[["country_iso_code","=","US"],"or",["country_iso_code","=","CA"]]]`<br>for more information about filters, please refer to [Domain Analytics Technologies API – Filters](https://docs.dataforseo.com/v3/domain_analytics/technologies/filters) |
| `order_by` | array | *results sorting rules*<br>optional field<br>available fields:<br>`domain_rank`, `domain`, `last_visited`, `country_iso_code`, `language_code`, `content_language_code`<br>possible sorting types:<br>`asc` – results will be sorted in the ascending order<br>`desc` – results will be sorted in the descending order<br>you should use a comma to set up a sorting type<br>example:<br>`["last_visited,desc"]`<br>default rule:<br>`["domain_rank,desc"]`<br>**note that you can set no more than three sorting rules in a single request**<br>you should use a comma to separate several sorting rules<br>example:<br>`["last_visited,desc","domain_rank,desc"]` |
| `limit` | integer | *the maximum number of returned domains*<br>optional field<br>default value: `100`<br>maximum value: `10000` |
| `offset` | integer | *offset in the results array of returned domains*<br>optional field<br>default value: `0`<br>if you specify the `10` value, the first ten domains in the results array will be omitted and the data will be provided for the successive domains;<br>**Note:** the maximum value is `9999`, the sum of `limit` and `offset` must not exceed `10000`;<br>use the `offset_token` if you would like to offset more results |
| `offset_token` | string | *token for subsequent requests*<br>optional field<br>provided in the identical filed of the response to each request;<br>use this parameter to avoid timeouts while trying to obtain over 100,000 results in a single request;<br>by specifying the unique `offset_token` value from the response array, you will get the subsequent results of the initial task;<br>`offset_token` values are unique for each subsequent task<br>**Note:** if the `offset_token` is specified in the request, all other parameters should be identical to the previous request<br>learn more about this parameter on our [Help Center](https://dataforseo.com/help-center/what-is-the-difference-between-the-offset-and-offset_token-parameters#offset_token) |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)<br>**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total *tasks* cost, USD* |
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
| `data` | object | *contains the same parameters that you specified in the POST request<br>* |
| ** `result`** | array | *array of results* |
| `total_count` | integer | *total number of relevant items in the database* |
| `items_count` | integer | *number of items in the results array* |
| `offset` | integer | *specified offset value* |
| `offset_token` | string | *token for subsequent requests*<br>by specifying the unique `offset_token` when setting a new task, you will get the subsequent results of the initial task;<br>`offset_token` values are unique for each subsequent task |
| `items` | array | *items array* |
| `type` | string | *type of the item = **‘domain_technology_item’*** |
| `domain` | string | *specified domain name*<br> |
| `title` | string | *domain meta title* |
| `description` | string | *domain meta description* |
| `meta_keywords` | array | *domain meta keywords* |
| `domain_rank` | string | *backlink rank of the target domain*<br>learn more about the metric and how it is calculated in [this help center article](https://dataforseo.com/help-center/what_is_rank_in_backlinks_api) |
| `last_visited` | string | *most recent date when our crawler visited the domain*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2022-10-10 12:57:46 +00:00` |
| `country_iso_code` | string | *domain ISO code*<br>ISO code of the country that target domain is determined to belong to |
| `language_code` | string | *domain language*<br>code of the language that target domain is determined to be associated with |
| `content_language_code` | string | *content language*<br>code of the language that content on the target domain is written with |
| `phone_numbers` | array | *phone numbers of the target*<br>contact phone numbers indicated on the target website |
| `emails` | array | *emails of the target*<br>emails indicated on the target website |
| `social_graph_urls` | array | *social media links and handles*<br>social media URLs detected in the social graphs of the target website |
| `technologies` | object | *technologies used by target domain*<br>contains objects with the names of technologies used on the website;<br>to get a full list of technologies and their structure, refer to the [technologies endpoint](https://docs.dataforseo.com/v3/domain_analytics/technologies/technologies/)<br> |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


#### Domain Technologies
*Source: [https://docs.dataforseo.com/v3/domain_analytics/technologies/domain_technologies/live/](https://docs.dataforseo.com/v3/domain_analytics/technologies/domain_technologies/live/)*
#### Domain Technologies

Using this endpoint you will get a list of technologies used in a particular domain.

POSThttps://api.dataforseo.com/v3/domain_analytics/technologies/domain_technologies/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/domain-analytics-api/domain-technologies-api) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The setting of tasks is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API requests per minute.
 
**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `target` | string | *target domain*<br>**required field**<br>domain name of the website to analyze<br>**Note:** results will be returned for the specified domain only<br> |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)<br>**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total *tasks* cost, USD* |
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
| `data` | object | *contains the same parameters that you specified in the POST request<br>* |
| ** `result`** | array | *array of results* |
| `type` | string | *type of the returned data item = **‘domain_technology_item’*** |
| `domain` | string | *specified domain name*<br> |
| `title` | string | *domain meta title* |
| `description` | string | *domain meta description* |
| `meta_keywords` | array | *domain meta keywords* |
| `domain_rank` | string | *backlink rank of the target domain*<br>learn more about the metric and how it is calculated in [this help center article](https://dataforseo.com/help-center/what_is_rank_in_backlinks_api) |
| `last_visited` | string | *most recent date when our crawler visited the domain*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2022-10-10 12:57:46 +00:00` |
| `country_iso_code` | string | *domain ISO code*<br>ISO code of the country that the target domain is determined to belong to |
| `language_code` | string | *domain language*<br>code of the language that the target domain is determined to be associated with |
| `content_language_code` | string | *content language*<br>code of the language that content on the target domain is written in |
| `phone_numbers` | array | *phone numbers of the target*<br>contact phone numbers indicated on the target website |
| `emails` | array | *emails of the target*<br>emails indicated on the target website |
| `social_graph_urls` | array | *social media links and handles*<br>social media URLs detected in the social graphs of the target website |
| `technologies` | object | *technologies used by target domain*<br>contains objects with the names of technologies used on the website<br>[see the full list of available technologies structured by groups and categories](https://docs.dataforseo.com/v3/domain_analytics/technologies/technologies/)<br> |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


#### Overview
*Source: [https://docs.dataforseo.com/v3/domain_analytics/whois/overview/](https://docs.dataforseo.com/v3/domain_analytics/whois/overview/)*
### Domain Analytics Whois API: Overview

This API provides Whois data, backlink stats, rankings, and traffic.

Domain Analytics Whois API will help you to get Whois and search results data for the domains matching the parameters you specify in the request.

Domain Analytics Whois API allows applying custom filtration to the dataset that will be retrieved. By using filters, you can effortlessly get exactly the data you need. For more information, please refer to the [Filters for Domain Analytics Whois API.](https://docs.dataforseo.com/v3/domain_analytics/whois/filters/)

You can also specify the number of results you want to retrieve, and indicate the necessary sorting parameters.

To find answers on common questions about Domain Analytics Whois API and find guidance on efficient use of its features, [visit our Help Center.](https://dataforseo.com/help-center/category/domain-analytics-api)

##### Methods

Domain Analytics Whois API supports only the Live method of data retrieval. It doesn’t require making separate POST and GET requests to the corresponding endpoints and delivers instant results.

You can send up to 2000 API calls per minute. Contact us if you would like to raise the limit.

##### Cost

The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/domain-analytics-api/domain-analytics-whois-api) page.

You can check your spending in your [account dashboard](https://app.dataforseo.com/api-access) or by making a separate call to [the User Data endpoint](https://docs.dataforseo.com/v3/appendix/user_data/?php).

---


#### Filters
*Source: [https://docs.dataforseo.com/v3/domain_analytics/whois/filters/](https://docs.dataforseo.com/v3/domain_analytics/whois/filters/)*
#### Filters for Domain Analytics Whois API

Here you will find all the necessary information about filters that can be used with Domain Analytics Whois API.

Note that filters are associated with a certain object in the `result` array, and should be specified accordingly.

Pricing

Your account will not be charged for using this API

GEThttps://api.dataforseo.com/v3/domain_analytics/whois/available_filters

You will receive the full list of filters by calling this API. You can also download the full list of possible filters [by this link.](https://cdn.dataforseo.com/v3/available_filters.php?api=domain_analytics/whois)

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

Below you will find a detailed description of the structure that should be used to specify filters for Domain Analytics Whois API. You will also find the types of parameters that can be used with each endpoint, and examples of pre-made filters.

**Description of the fields:**

| Field name | Type | Description |
| --- | --- | --- |
| `filters` | array | *array of results filtering parameters*<br>optional field<br>**you can add several filters at once (8 filters maximum)**<br>you should set a logical operator `and`, `or` between the conditions<br>filters have the following structure:<br>`[``$item_array``.``$results_array``.``$parameter_field``,` `$filter_operator``,` `$filter_value``]`<br>you should use the `.` and `,` characters as separators<br>example:<br>`["metrics.organic.pos_1", ">=", 50]` |
| `$item_array` | str | *item name in the filter*<br>optional field<br>possible values:<br>`keyword_data`, `ranked_serp_element` |
| `$results_array` | str | *results array in the filter*<br>optional field<br>possible values:<br>`keyword`, `keyword_info`, `check_url`, `se_results_count`, `serp_item`, `metrics` |
| `$parameter_field` | str | *parameter field in the filter*<br>optional field<br>**required field if the filter is applied**<br>the parameter in the superordinate `$results_array` or `item_array`<br>represents the field you want to filter the results by |
| `$filter_operator` | str | *operator in the filter*<br>optional field<br>**required field if the filter is applied**<br>available filter operators:<br>• if **`bool`**: `=`, `<>`<br>• if **`num`**: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>• if **`str`**: `like`, `not_like`, `in`, `not_in`, `=`, `<>`, `regex`, `not_regex`<br>• if **`array.str`**: `has`, `has_not`<br>• if **`array.num`**: `has`, `has_not`<br>• if **`time`**: `<`, `>``time` should be specified in the format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2021-01-29 15:02:37 +00:00`<br>if you specify `in` or `not_in` operator, the `$filter_value` should be specified as an array;<br>example:<br>`["metrics.organic.etv","in",[10,100]]`<br>`regex` and `not_regex` operator can be specified with `string` values using the [RE2 regex](https://github.com/google/re2/wiki/Syntax) syntax;<br>**Note:** the maximum limit for the number of characters you can specify in `regex` and `not_regex` is **1000**;<br>`like` and `not_like` operators require adding `%` character to get accurate results;<br>example:<br>`["domain", "like", "%seo%"]` return `keyword_data` items that contain “seo” in the `domain` field<br>`["domain", "not_like", "%seo%"]` do not return domains that contain “seo” |
| `$filter_value` | num<br>str<br>bool<br>array.str | *filtering value*<br>optional field<br>**required field if the filter is applied** |
| **available filters** | num<br>str<br>bool | *the list of available filters for the [Domain Analytics Whois Overview](https://docs.dataforseo.com/v3/domain_analytics/whois/overview/live/) endpoint:*<br>`["domain", "like", "%seo%"]<br>["expiration_datetime",">","2021-02-15 01:00:00 +00:00"]<br>["created_datetime","<","2019-03-15 01:00:00 +00:00"]<br>["registered","=",true]<br>["tld","=","com"]<br>["metrics.organic.etv",">",100]<br>["metrics.paid.etv",">",0]`<br>You can get the full list of possible filters [by this link](https://cdn.dataforseo.com/v3/available_filters.php?api=dataforseo_labs) |

> The list of available filtration parameters:

---


#### Whois Overview
*Source: [https://docs.dataforseo.com/v3/domain_analytics/whois/overview/live/](https://docs.dataforseo.com/v3/domain_analytics/whois/overview/live/)*
#### Domain Whois Overview

This endpoint will provide you with Whois data enriched with backlink stats, and ranking and traffic info from organic and paid search results. Using this endpoint you will be able to get all these data for the domains matching the parameters you specify in the request.

POSThttps://api.dataforseo.com/v3/domain_analytics/whois/overview/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/domain-analytics-api/domain-analytics-whois-api) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute.

You can specify the number of results you want to retrieve, set filters and indicate sorting parameters.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `limit` | integer | *the maximum number of returned domains*optional fielddefault value: `100`maximum value: `1000` |
| `offset` | integer | *offset in the results array of returned items*optional fielddefault value: `0`if you specify the `10` value, the first ten `items` in the results array will be omitted and the data will be provided for the successive items;**Note:** we recommend using this parameter only when retrieving up to 10,000 results for retrieving over 10,000 results, use the `offset_token` instead |
| `offset_token` | string | *token for subsequent requests*optional fieldprovided in the identical filed of the response to each request;use this parameter to avoid timeouts while trying to obtain over 100,000 results in a single request;by specifying the unique `offset_token` value from the response array, you will get the subsequent results of the initial task;`offset_token` values are unique for each subsequent task**Note:** if the `offset_token` is specified in the request, all other parameters should be identical to the previous requestlearn more about this parameter on our [Help Center](https://dataforseo.com/help-center/what-is-the-difference-between-the-offset-and-offset_token-parameters#offset_token) |
| `filters` | array | *array of results filtering parameters*optional field**you can add several filters at once (8 filters maximum)**you should set a logical operator `and`, `or` between the conditionsthe following operators are supported:`regex`, `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`, `like`, `not_like`you can use the `%` operator with `like` and `not_like` to match any string of zero or more characters |
| `order_by` | array | *results sorting rules*optional fieldyou can use the same values as in the `filters` array to sort the resultspossible sorting types:`asc` - results will be sorted in the ascending order`desc` - results will be sorted in the descending orderthe comma is used as a separatorexample:`["metrics.organic.pos_1,desc"]`default rule:`["metrics.organic.count,desc"]`**note that you can set no more than three sorting rules in a single request**you should use a comma to separate several sorting rulesexample:`["expiration_datetime,asc","metrics.organic.etv,desc","metrics.organic.pos_1,desc"]` |
| `tag` | string | *user-defined task identifier*optional field*the character limit is 255*you can use this parameter to identify the task and match it with the resultyou will find the specified `tag` value in the `data` object of the response |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total tasks cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier***unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task *generated by DataForSEO; can be within the following range: 10000-60000you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `total_count` | integer | *total amount of results in our database relevant to your request* |
| `items_count` | integer | *the number of results returned in the `items` array* |
| `offset` | integer | * results offset value specified in POST request* |
| `offset_token` | object | *token for subsequent requests*by specifying the unique `offset_token` when setting a new task, you will get the subsequent results of the initial task;`offset_token` values are unique for each subsequent task |
| **`items`** | array | *contains ranking and traffic data* |
| `domain` | string | *domain name* |
| `created_datetime` | string | *date and time of registration*date and time (in the [ISO 8601 format](https://en.wikipedia.org/wiki/ISO_8601)) when the domain was first registered example: `"1997-03-29 03:00:00 +00:00"` |
| `changed_datetime` | string | *date and time when the domain entry was changed*date and time (in the [ISO 8601 format](https://en.wikipedia.org/wiki/ISO_8601)) when the domain entry was last modifiedexample: `"2021-01-14 08:36:28 +00:00"` |
| `expiration_datetime` | string | *date and time when the domain will expire*date and time (in the [ISO 8601 format](https://en.wikipedia.org/wiki/ISO_8601)) when the domain is due to expire example: `"2022-11-26 17:21:23 +00:00"` |
| `updated_datetime` | string | *date and time when the domain was updated*date and time (in the [ISO 8601 format](https://en.wikipedia.org/wiki/ISO_8601)) when the domain was last updated example: `"2021-01-29 13:59:38 +00:00"` |
| `first_seen` | string | *date and time when our crawler found the domain for the first time*in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”example: `"2019-11-15 12:57:46 +00:00"` |
| `epp_status_codes` | array | *extensive provisioning protocol status codes*the status of a domain name registration [as defined by ICANN](https://www.icann.org/resources/pages/epp-status-codes-2014-06-16-en) |
| `tld` | string | *top-level domain*top-level domain in the [DNS root zone](https://www.iana.org/domains/root/db) |
| `registered` | boolean | *domain registration status*if `false`, the domain name registration has expired**Note: expired domains will remain in the database for only a short period of time** |
| `registrar` | string | *domain registrar*if `null`, the domain registrar is unknownexample:`NameCheap, Inc.` |
| **`metrics`** | object | *ranking data relevant to the specified domain* |
| **`organic`** | object | *ranking and traffic data from organic search* |
| `pos_1` | integer | *number of organic SERPs where the domain ranks #1* |
| `pos_2_3` | integer | *number of organic SERPs where the domain ranks #2-3* |
| `pos_4_10` | integer | *number of organic SERPs where the domain ranks #4-10* |
| `pos_11_20` | integer | *number of organic SERPs where the domain ranks #11-20* |
| `pos_21_30` | integer | *number of organic SERPs where the domain ranks #21-30* |
| `pos_31_40` | integer | *number of organic SERPs where the domain ranks #31-40* |
| `pos_41_50` | integer | *number of organic SERPs where the domain ranks #41-50* |
| `pos_51_60` | integer | *number of organic SERPs where the domain ranks #51-60* |
| `pos_61_70` | integer | *number of organic SERPs where the domain ranks #61-70* |
| `pos_71_80` | integer | *number of organic SERPs where the domain ranks #71-80* |
| `pos_81_90` | integer | *number of organic SERPs where the domain ranks #81-90* |
| `pos_91_100` | integer | *number of organic SERPs where the domain ranks #91-100* |
| `etv` | float | *estimated traffic volume*estimated organic monthly traffic to the domaincalculated as the product of CTR (click-through-rate) and search volume values of all keywords the domain ranks forlearn more about how the metric is calculated in [this help center article](https://dataforseo.com/help-center/how-is-etv-calculated) |
| `count` | integer | *total count of organic SERPs that contain the domain* |
| `estimated_paid_traffic_cost` | float | *estimated cost of converting organic search traffic into paid*represents the estimated monthly cost of running ads (USD) for all keywords a domain ranks forthe metric is calculated as the product of organic `etv` and paid `cpc` values and indicates the cost of driving the estimated volume of monthly organic traffic through PPC advertising in Google Searchlearn more about how the metric is calculated in [this help center article](https://dataforseo.com/help-center/how-is-traffic-cost-calculated) |
| **`paid`** | object | *ranking and traffic data from paid search* |
| `pos_1` | integer | *number of paid SERPs where the domain ranks #1* |
| `pos_2_3` | integer | *number of paid SERPs where the domain ranks #2-3* |
| `pos_4_10` | integer | *number of paid SERPs where the domain ranks #4-10* |
| `pos_11_20` | integer | *number of paid SERPs where the domain ranks #11-20* |
| `pos_21_30` | integer | *number of paid SERPs where the domain ranks #21-30* |
| `pos_31_40` | integer | *number of paid SERPs where the domain ranks #31-40* |
| `pos_41_50` | integer | *number of paid SERPs where the domain ranks #41-50* |
| `pos_51_60` | integer | *number of paid SERPs where the domain ranks #51-60* |
| `pos_61_70` | integer | *number of paid SERPs where the domain ranks #61-70* |
| `pos_71_80` | integer | *number of paid SERPs where the domain ranks #71-80* |
| `pos_81_90` | integer | *number of paid SERPs where the domain ranks #81-90* |
| `pos_91_100` | integer | *number of paid SERPs where the domain ranks #91-100* |
| `etv` | float | *estimated traffic volume*estimated paid monthly traffic to the domaincalculated as the product of CTR (click-through-rate) and search volume values of all keywords the domain ranks forlearn more about how the metric is calculated in [this help center article](https://dataforseo.com/help-center/how-is-etv-calculated) |
| `count` | integer | *total count of paid SERPs that contain the domain* |
| `estimated_paid_traffic_cost` | float | *estimated cost of monthly search traffic*represents the estimated cost of paid monthly traffic (USD) based on `etv` and `cpc` valueslearn more about how the metric is calculated in [this help center article](https://dataforseo.com/help-center/how-is-traffic-cost-calculated) |
| **`backlinks_info`** | object | *backlink data for the returned domain* |
| `referring_domains` | integer | *number of referring domains* |
| `referring_main_domains` | integer | *number of referring main domains* |
| `referring_pages` | integer | *number of referring pages* |
| `dofollow` | integer | *number of dofollow links* |
| `backlinks` | integer | *total number of backlinks*the total number of backlinks, including dofollow and nofollow links |
| `time_update` | string | *date and time when backlink data was updated*in the UTC format: "yyyy-mm-dd hh-mm-ss +00:00"example:`2019-11-15 12:57:46 +00:00` |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---
