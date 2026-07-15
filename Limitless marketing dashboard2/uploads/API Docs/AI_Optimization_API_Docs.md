# AI Optimization API Documentation
*Consolidated main text documentation of AI Optimization API compiled from docs.dataforseo.com*

---


### Overview
*Source: [https://docs.dataforseo.com/v3/ai_optimization/overview/](https://docs.dataforseo.com/v3/ai_optimization/overview/)*
### AI Optimization API: Overview

This API is the ultimate source of data for AI search optimization

DataForSEO AI Optimization API provides data for keyword discovery, conversational optimization, and real-time LLM benchmarking.

It encompasses the following purpose-driven APIs:

• [LLM Responses API](https://docs.dataforseo.com/v3/ai_optimization/llm_responses/overview/) enables real-time generation of structured responses from leading LLMs, including ChatGPT, Claude, Gemini, and Perplexity, based on your specified input parameters.

• [LLM Scraper API](https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/overview/) provides results from scraped ChatGPT searches, based on the keyword and other input parameters.

• [AI Keyword Data API](https://docs.dataforseo.com/v3/ai_optimization/ai_keyword_data/overview/) delivers search volume estimates and user intent insights based on keyword usage in AI tools like ChatGPT and other large language models.

• [LLM Mentions API](https://docs.dataforseo.com/v3/ai_optimization/llm_mentions/overview/) provides data on keyword, brand and website mentions in LLMs, including metrics like AI search volume, impressions and mentions count.

To find answers on common questions about AI Optimization API and find guidance on most efficient use, [visit our Help Center.](https://dataforseo.com/help-center/category/ai-optimization-api)

##### Methods

The cost of using AI Optimization API depends on the selected method and priority of task execution. Available methods and priorities are described below.

DataForSEO has two main methods to deliver the results: Standard and Live.

If your system requires delivering instant results, **the Live method** is the best solution for you. Unlike the Standard method, this method doesn’t require making separate POST and GET requests to the corresponding endpoints.

If you don’t need to receive data in real-time, you can use **the Standard method** of data retrieval. This method requires making separate POST and GET requests, but it’s more affordable. Using this method, you can retrieve the results after our system collects them.

Alternatively, you can specify `pingback_url` or `postback_url` when setting a task, and we will notify you on completion of tasks or send them to you respectively.

If you need to set several tasks, you can receive the list of id for all completed tasks using **‘Tasks Ready’** endpoint, and then collect the results of each separate task using ‘Task GET’ endpoint.

AI Keyword Data API and LLM Mentions API support only the Live method of data retrieval. LLM Responses and LLM Scraper APIs support both Standard and Live methods, depending on the selected AI platform.

##### Cost

The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/ai-optimization) page. You can check your spending in your [account dashboard](https://app.dataforseo.com/api-access) or by making a separate call to [the User Data endpoint](https://docs.dataforseo.com/v3/appendix/user_data/?php)

You can test AI Optimization API for free using DataForSEO [Sandbox.](https://docs.dataforseo.com/v3/appendix/sandbox/)

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

---


#### Overview
*Source: [https://docs.dataforseo.com/v3/ai_optimization/ai_keyword_data/overview/](https://docs.dataforseo.com/v3/ai_optimization/ai_keyword_data/overview/)*
### AI Keyword Data API: Overview

This API is the ultimate source of keyword data for AI search optimization

AI Keyword Data API provides data on keyword search trends in AI platforms. You can use it to gain a deeper understanding of how users phrase queries in conversational interfaces.

The endpoints of this API currenly include:

• [AI Keyword Search Volume endpoint](https://docs.dataforseo.com/v3/ai_optimization/ai_keyword_data/keywords_search_volume/live/) provides search volume data for your target keywords, reflecting their estimated usage in AI tools.

Learn more about the AI Search Volume metric [here.](https://dataforseo.com/help-center/what-is-ai-search-volume-in-dataforseo)

To find answers on common questions about AI Optimization API and find guidance on most efficient use, [visit our Help Center.](https://dataforseo.com/help-center/category/ai-optimization-api)

##### Methods

AI Keyword Data API supports only the Live method of data retrieval. It doesn’t require making separate POST and GET requests to the corresponding endpoints and delivers instant results.

You can send up to 2000 API calls per minute. Contact us if you would like to raise the limit. Note that the maximum number of requests that can be sent simultaneously is limited to 30.

##### Cost

The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/ai-optimization/ai-keyword-search-volume) page. You can check your spending in your [account dashboard](https://app.dataforseo.com/api-access) or by making a separate call to [the User Data endpoint](https://docs.dataforseo.com/v3/appendix/user_data/?php)

You can test AI Keyword Data API for free using DataForSEO [Sandbox.](https://docs.dataforseo.com/v3/appendix/sandbox/)

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

---


#### Locations and Languages
*Source: [https://docs.dataforseo.com/v3/ai_optimization/ai_keyword_data/locations_and_languages/](https://docs.dataforseo.com/v3/ai_optimization/ai_keyword_data/locations_and_languages/)*
#### AI Keyword Data API Locations and Languages List

Using this endpoint you can get the full list of locations and languages supported in AI Keyword Data API.

##### **Note:** All locations in Russia and Belarus are no longer supported across all DataForSEO services due to the invasion of Ukraine.

GEThttps://api.dataforseo.com/v3/ai_optimization/ai_keyword_data/locations_and_languages

Pricing

Your account will not be charged for using this API

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information about available locations and languages.

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
| `location_code` | integer | *location code* |
| `location_name` | string | *full name of the location* |
| `available_languages` | array | *supported languages*<br>contains the languages which are supported for a specific location |
| `language_name` | string | *language name* |
| `language_code` | string | *language code according to [ISO 639-1](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes)* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


#### Keywords Search Volume
*Source: [https://docs.dataforseo.com/v3/ai_optimization/ai_keyword_data/keywords_search_volume/live/](https://docs.dataforseo.com/v3/ai_optimization/ai_keyword_data/keywords_search_volume/live/)*
#### Live Keyword Search Volume AI Keyword Data

This endpoint provides search volume data for your target keywords, reflecting their estimated usage in AI tools.

For each specified keyword, you will get AI search volume rate for the last month and AI search volume trend for the previous 12 months. The AI Search Volume values are calculated using statistical data from questions in the ‘People Also Ask’ SERP element. Learn more about this metric [here.](https://dataforseo.com/help-center/what-is-ai-search-volume-in-dataforseo)

POSThttps://api.dataforseo.com/v3/ai_optimization/ai_keyword_data/keywords_search_volume/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/ai-optimization/ai-keyword-search-volume) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute. The maximum number of requests that can be sent simultaneously is limited to 30.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `keywords` | array | *keywords***required field**UTF-8 encodingThe maximum number of keywords you can specify: 1000;The maximum number of characters in a single keyword: 250;The keywords will be converted to lowercase format;learn more about rules and limitations of `keyword` and `keywords` fields in DataForSEO APIs in this [Help Center article](https://dataforseo.com/help-center/rules-and-limitations-of-keyword-and-keywords-fields-in-dataforseo-apis) |
| `location_name` | string | *full name of the location***required field if you don't specify** `location_code`**Note:** it is required to specify either `location_name` or `location_code`you can receive the list of available locations with their `location_name` by making a separate request to the`[https://api.dataforseo.com/v3/ai_optimization/ai_keyword_data/locations_and_languages](https://api.dataforseo.com/v3/ai_optimization/ai_keyword_data/locations_and_languages)`example:`United Kingdom` |
| `location_code` | integer | *unique location identifier***required field if you don't specify** `location_name`**Note:** it is required to specify either `location_name` or `location_code`you can receive the list of available locations with their `location_code` by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/ai_keyword_data/locations_and_languages](https://api.dataforseo.com/v3/ai_optimization/ai_keyword_data/locations_and_languages)`example:`2840` |
| `language_name` | string | *full name of the language***required field if you don't specify** `language_code`**if you use this field, you don't need to specify** `language_code`you can receive the list of available languages with their `language_name` by making a separate request to the`[https://api.dataforseo.com/v3/ai_optimization/ai_keyword_data/locations_and_languages](https://api.dataforseo.com/v3/ai_optimization/ai_keyword_data/locations_and_languages)`example:`English` |
| `language_code` | string | *language code***required field if you don't specify** `language_name`**if you use this field, you don't need to specify** `language_name`you can receive the list of available languages with their `language_code` by making a separate request to the`[https://api.dataforseo.com/v3/ai_optimization/ai_keyword_data/locations_and_languages](https://api.dataforseo.com/v3/ai_optimization/ai_keyword_data/locations_and_languages)`example:`en` |
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
| `location_code` | integer | *location code in a POST array* |
| `language_code` | string | *language code in a POST array* |
| `items_count` | integer | *number of results returned in the `items` array* |
| **`items`** | array | *contains specified keywords with their AI search volume rates* |
| `keyword` | string | *specified keyword* |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/what-is-ai-search-volume-in-dataforseo) |
| **`ai_monthly_searches`** | array | *monthly AI search volume rates*array of objects with AI search volume rates in a certain month of a year |
| `year` | integer | *year* |
| `month` | integer | *month* |
| `ai_search_volume` | integer | *AI search volume rate in a certain month of a year*learn more about this metric [here](https://dataforseo.com/help-center/what-is-ai-search-volume-in-dataforseo) |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


#### Overview
*Source: [https://docs.dataforseo.com/v3/ai_optimization/llm_mentions/overview/](https://docs.dataforseo.com/v3/ai_optimization/llm_mentions/overview/)*
### LLM Mentions API: Overview

This API is the ultimate source of LLM mentions data for AI search optimization

LLM Mentions API provides data on keyword, brand and website mentions in LLMs, including metrics like LLM chat mentions, sources and AI search volume. You can use it to assess how often a business is mentioned in AI responses, discover traffic potential of mentions and track changes in AI visibility over time.

The endpoints of this API currently include:

• [Search Mentions endpoint](https://docs.dataforseo.com/v3/ai_optimization/llm_mentions/search/live/) provides detailed and structured mentions data for target keywords and domains, including mentions count and quoted links from AI responses.

• [Aggregated Metrics endpoint](https://docs.dataforseo.com/v3/ai_optimization/llm_mentions/aggregated_metrics/live/) provides a consolidated overview of key mention metrics across different dimensions, such as location, language, AI platform, and source domains.

• [Cross Aggregated Metrics endpoint](https://docs.dataforseo.com/v3/ai_optimization/llm_mentions/cross_aggregated_metrics/live/) provides consolidated mention metrics for multiple target domains, keywords simultaneously. It allows to compare and assess mention metrics across multiple targets in a single request.

• [Top Domains endpoint](https://docs.dataforseo.com/v3/ai_optimization/llm_mentions/top_domains/live/) provides aggregated mentions metrics grouped by the most frequently mentioned domains for the keyword or domain you specify.

• [Top Pages endpoint](https://docs.dataforseo.com/v3/ai_optimization/llm_mentions/top_pages/live/) provides aggregated mentions metrics grouped by the top mentioned pages for the specified keyword or domain.

To find answers on common questions about AI Optimization API and find guidance on most efficient use, [visit our Help Center.](https://dataforseo.com/help-center/category/ai-optimization-api)

##### Methods

LLM Mentions API supports only the Live method of data retrieval. It doesn’t require making separate POST and GET requests to the corresponding endpoints and delivers instant results.

You can send up to 2000 API calls per minute. Contact us if you would like to raise the limit. Note that the maximum number of requests that can be sent simultaneously is limited to 30.

##### Cost

The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/ai-optimization/llm-mentions) page. You can check your spending in your [account dashboard](https://app.dataforseo.com/api-access) or by making a separate call to [the User Data endpoint](https://docs.dataforseo.com/v3/appendix/user_data/?php)

You can test LLM Mentions API for free using DataForSEO [Sandbox.](https://docs.dataforseo.com/v3/appendix/sandbox/)

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

---


#### Filters
*Source: [https://docs.dataforseo.com/v3/ai_optimization/llm_mentions/filters/](https://docs.dataforseo.com/v3/ai_optimization/llm_mentions/filters/)*
#### LLM Mentions Filters List

Here you will find all the necessary information about filters that can be used with AI Optimization LLM Mentions API endpoints.

Please, keep in mind that filters are associated with a certain object in the `result` array, and should be specified accordingly.

We recommend learning more about how to use filters in [this Help Center article](https://dataforseo.com/help-center/using-filters).

**Note that it is not possible to use the following types of fields as sorting rules in `order_by`: `array.str`, `array.num`.**

Pricing

Your account will not be charged for using this API

GEThttps://api.dataforseo.com/v3/ai_optimization/llm_mentions/available_filters

You will receive the full list of filters by calling this API. You can also download the full list of possible filters [by this link.](https://cdn.dataforseo.com/v3/available_filters.php?api=ai_optimization/llm_mentions)

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

Below you will find a detailed description of the structure that should be used to specify `filters` when setting tasks with AI Optimization LLM Mentions API. You will also find the types of parameters that can be used with each endpoint, and examples of pre-made filters.

**Description of the fields:**

| Field name | Type | Description |
| --- | --- | --- |
| `filters` | array | *array of results filtering parameters*<br>optional field<br>**you can add several filters at once (8 filters maximum)**<br>you should set a logical operator `and`, `or` between the conditions<br>filters have the following structure:<br>`[`$parameter_field``,` `$filter_operator``,` `$filter_value``]`<br>you should use the `.` and `,` symbols as separators<br>example:<br>`["ai_search_volume", ">=", 1000]`` |
| `$parameter_field` | str | *parameter field in the filter*<br>optional field<br>**required field if the filter is applied**<br>the parameter in the superordinate `$results_array`<br>represents the field you want to filter the results by<br>possible values:<br>`platform`, `location_code`, `language_code`, `ai_search_volume`, `first_response_at`, `last_response_at` |
| `$filter_operator` | str | *operator in the filter*<br>optional field<br>**required field if the filter is applied**<br>available filter operators:<br>• if **`num`**: `<`, `<=`, `>`, `>=`, `=`, `<>`, `in`, `not_in`<br>• if **`str`**: `match`, `not_match`, `like`, `not_like`, `ilike`, `not_ilike`, `in`, `not_in`, `=`, `<>`, `regex`, `not_regex`<br>• if **`time`**: `<`, `<=`, `>`, `>=`<br>note: `time` should be specified in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2025-10-21 06:25:30 +00:00`<br>if you specify `in` or `not_in` operator, the `$filter_value` should be specified as an array<br>example:<br>`["ai_search_volume","in",[10,1000]]`<br>`regex` and `not_regex` operators can be specified with `string` values using the [RE2 regex](https://github.com/google/re2/wiki/Syntax) syntax;<br>**Note:** the maximum limit for the number of characters you can specify in `regex` and `not_regex` is **1000**;<br>example:<br>string contains keywords: ` ["language_code", "regex", "(how|what|when)"]`<br>string does not contain keywords: ` ["language_code", "not_regex", "(how|what|when)"]` |
| `$filter_value` | num<br>str<br>bool<br>time | *filtering value*<br>optional field<br>**required field if the filter is applied** |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The list of available filtration parameters:

---


#### Locations and Languages
*Source: [https://docs.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages/](https://docs.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages/)*
#### LLM Mentions Locations and Languages List

Using this endpoint you can get the full list of locations and languages supported in AI Optimization LLM Mentions API.

**Note:**`chat_gpt` data is available for the `United States` and `English` only.

##### **Note:** All locations in Russia and Belarus are not supported across all DataForSEO services due to the invasion of Ukraine.

GEThttps://api.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages

Pricing

Your account will not be charged for using this API

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information about available locations and languages.

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *general informational message*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total tasks cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier***unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*generated by DataForSEO; can be within the following range: 10000-60000you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the parameters passed in the URL of the GET request* |
| **`result`** | array | *array of results* |
| `location_code` | integer | *location code* |
| `location_name` | string | *full name of the location* |
| **`available_languages`** | array | *supported languages*contains the languages which are supported for a specific location |
| `available_platforms` | array | *supported LLM platforms*contains the sources of data supported for a specific location and language combinationonly `google` and `chat_gpt` are currently available |
| `language_name` | string | *language name* |
| `language_code` | string | *language code according to [ISO 639-1](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes)* |
| `responses_count` | integer | *number of LLM responses*the number of LLM responses available in the database for the certain location and language parameters |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


#### Search
*Source: [https://docs.dataforseo.com/v3/ai_optimization/llm_mentions/search/live/](https://docs.dataforseo.com/v3/ai_optimization/llm_mentions/search/live/)*
#### Live LLM Mentions Search

Live LLM Mentions Search endpoint provides mention data and related metrics from AI searches. The results are specific to the selected platform (`google` for Google’s AI Overview or `chat_gpt` for ChatGPT), as well as location and language parameters (see [the List of Locations & Languages](https://docs.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages)).

POSThttps://api.dataforseo.com/v3/ai_optimization/llm_mentions/search/live

Pricing

The cost of the task can be calculated on the [Pricing page](https://dataforseo.com/pricing/ai-optimization/llm-mentions).

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute, each Live LLM Mentions API call can contain only one task.

**Execution time for tasks set with the Live LLM Mentions endpoint is currently up to 120 seconds.**

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| **`target`** | array | *array of objects containing target entities***required field**you can specify **up to 10 entities (objects)** in the `target` fieldone target entity can contain either one `domain` or one `keyword` and related parametersexamples: target array with a domain entity`[{"domain": "en.wikipedia.org", "search_filter": "exclude"}]`target array with a keyword entity`[{"keyword": "bmw", "search_scope": ["question"], "match_type ": "partial_match"}]`target array with multiple entities`[{"domain": "en.wikipedia.org", "search_filter": "exclude"}, {"keyword": "bmw", "match_type ": "partial_match", "search_scope": ["answer"]}]` |
| **`domain_entity`** | object | *domain entity in the target array*example:`{"domain": "en.wikipedia.org", "search_filter": "exclude", "search_scope": ["sources"]}` |
| `domain` | string | *target domain***required field if you don't specify `keyword`**you can specify **up to 63 characters** in the `domain` field;a domain should be specified without `https://` and `www.` |
| `search_filter` | string | *target domain search filter*optional fieldpossible values:`include`, `exclude`default value: `include` |
| `search_scope` | array | *target domain search scope*optional fieldpossible values:`any`, `sources`, `search_results`default value: `any` |
| `include_subdomains` | boolean | *indicates if the subdomains of the target `domain` will be included in the search*optional fieldif set to `true`, the subdomains will be included in the searchdefault value: `false` |
| **`keyword_entity`** | object | *keyword entity in the target array*example:`{"keyword": "bmw", "search_filter": "include", "search_scope": ["question"], "match_type ": "partial_match"}` |
| `keyword` | string | *target keyword***required field if you don't specify `domain`**you can specify **up to 250 characters** in the `keyword` fieldall %## will be decoded (plus character ‘+’ will be decoded to a space character)if you need to use the “%” character for your `keyword`, please specify it as “%25”;if you need to use the “+” character for your `keyword`, please specify it as “%2B”learn more about rules and limitations of `keyword` and `keywords` fields in DataForSEO APIs in this [Help Center article](https://dataforseo.com/help-center/rules-and-limitations-of-keyword-and-keywords-fields-in-dataforseo-apis) |
| `search_filter` | string | *target keyword search filter*optional fieldpossible values:`include`, `exclude`default value: `include` |
| `search_scope` | array | *target keyword search scope*optional fieldpossible values:`any`, `question`, `answer`, `brand_entities`, `fan_out_queries`default value: `any` |
| `match_type` | string | *target keyword match type*defines how the specified keyword is matchedoptional fieldpossible values:`word_match` - full-text search for terms that match the specified seed keyword with additional words included before, after, or within the key phrase (e.g., search for "light" will return results with "light bulb", "light switch");`partial_match` - substring search that finds all instances containing the specified sequence of characters, even if it appears inside a longer word (e.g., search for "light" will return results with "lighting", "highlight");default value: `word_match` |
| `location_name` | string | *full name of search location*optional fieldif you use this field, you don't need to specify `location_code`if you don't specify this field, the `location_code` with `2840` value will be used by default;you can receive the list of available locations of the search engine with their `location_name` by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages](https://api.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages)`**Note: `chat_gpt` data is available for `United States` only** |
| `location_code` | integer | *search location code*optional fieldif you use this field, you don't need to specify `location_name`you can receive the list of available locations of the search engine with their `location_code` by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages](https://api.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages)`default value: `2840`**Note: `chat_gpt` data is available for `2840` only** |
| `language_name` | string | *full name of search language*optional fieldif you use this field, you don't need to specify `language_code`;if you don't specify this field, the `language_code` with `en` value will be used by default;you can receive the list of available languages of the search engine with their `language_name` by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages](https://api.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages)`**Note: `chat_gpt` data is available for `English` only** |
| `language_code` | string | *search language code*optional fieldif you use this field, you don't need to specify `language_name`;you can receive the list of available languages of the search engine with their `language_code`_by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages](https://api.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages)`default value: `en`**Note: `chat_gpt` data is available for `en` onlyn** |
| `platform` | string | *target platform*optional fieldpossible values:`chat_gpt`, `google`default value: `google`**Note:** the data returned depends on the selected platform**Note #2:**`chat_gpt` data is available for the `United States` and `English` only |
| `filters` | array | *array of results filtering parameters*optional field**you can add several filters at once (8 filters maximum)**you should set a logical operator `and`, `or` between the conditionsthe following operators are supported:`=`, `<>`, `in`, `not_in`, `like`, `not_like`, `ilike`, `not_ilike`, `match`, `not_match`you can use the `%` operator with `like` and `not_like` to match any string of zero or more charactersexample:`["ai_search_volume",">","1000"]`The full list of possible filters is available [here.](https://docs.dataforseo.com/v3/ai_optimization/llm_mentions/filters/) |
| `order_by` | array | *results sorting rules*optional fieldyou can use the same values as in the `filters` array to sort the resultspossible sorting types:`asc` - results will be sorted in the ascending order`desc` - results will be sorted in the descending orderyou should use a comma to set up a sorting typeexample:`["ai_search_volume,desc"]`**note that you can set no more than three sorting rules in a single request**you should use a comma to separate several sorting rules |
| `offset` | integer | *offset in the results array of the returned mentions data*optional fielddefault value: `0`example: if you specify the `10` value, the first ten mentions objects in the results array will be omitted and the data will be provided for the successive objects;**Note:** the maximum value is `9,000`, use the `search_after_token` if you would like to offset more results |
| `search_after_token` | string | *token for subsequent requests*optional fieldprovided in the identical filed of the response to each request;use this parameter to avoid timeouts while trying to obtain over `20,000` results in a single request;by specifying the unique `search_after_token` value from the response array, you will get the subsequent results of the initial task;`search_after_token` values are unique for each subsequent task ;**Note:** if the `search_after_token` is specified in the request, all other parameters should be identical to the previous request |
| `limit` | integer | *the maximum number of returned objects*optional fielddefault value: `100`maximum value: `1000` |
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
| `status_code` | integer | *status code of the task*generated by DataForSEO; can be within the following range: 10000-60000you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `total_count` | integer | *total amount of results relevant the request* |
| `current_offset` | integer | *the number of mentions objects that are omitted in the `items` array* |
| `search_after_token` | string | *token for subsequent requests*by specifying the unique `search_after_token` when setting a new task, you will get the subsequent results of the initial task;`search_after_token` values are unique for each subsequent task |
| `items_count` | integer | *the number of results returned in the `items` array* |
| **`items`** | array | *contains relevant mentions data* |
| `platform` | string | *platform received in a POST array* |
| `model_name` | string | *name of the AI model from which the data was retrieved***Note:** for the `google` platform type, the value is always `google_ai_overview` |
| `location_code` | integer | *location code in a POST array* |
| `language_code` | string | *language code in a POST array* |
| `question` | string | *relevant question* |
| `answer` | string | *relevant answer in markdown format*content of the result formatted in the [markdown markup language](https://en.wikipedia.org/wiki/Markdown) |
| **`sources`** | array | *array of sources*the sources the model cited or relied on in its final answerlearn more about the sources and how to retrieve LLM citation data at our [Help Center](https://dataforseo.com/help-center/how-to-get-llm-citation-data-with-llm-mentions-api) |
| `snippet` | string | *source description* |
| `source_name` | string | *source name* |
| `thumbnail` | string | *source thumbnail* |
| `markdown` | string | *content of the element in markdown format*content of the result formatted in the [markdown markup language](https://en.wikipedia.org/wiki/Markdown) |
| `position` | integer | *position in the results* |
| `title` | string | *source title* |
| `domain` | string | *source domain* |
| `url` | string | *source URL* |
| `publication_date` | string | *date and time when the result was published*in the format: “year-month-date:minutes:UTC_difference_hours:UTC_difference_minutes”example:`2019-11-15 12:57:46 +00:00` |
| **`search_results`** | array | *array of search results*all web search outputs the model retrieved when looking up information, including duplicates and unused entries |
| `description` | string | *result description* |
| `breadcrumb` | string | *breadcrumb* |
| `position` | integer | *position in the results* |
| `title` | string | *result title* |
| `domain` | string | *result domain* |
| `url` | string | *result URL* |
| `publication_date` | string | *date and time when the result was published*in the format: “year-month-date:minutes:UTC_difference_hours:UTC_difference_minutes”example:`2019-11-15 12:57:46 +00:00` |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| **`monthly_searches`** | array | *monthly AI search volume rates*array of objects with AI search volume rates in a certain month of a year |
| `year` | integer | *year* |
| `month` | integer | *month* |
| `search_volume` | integer | *AI search volume rate in a certain month of a year*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `first_response_at` | string | *date and time when the response data was first recorded*in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”example:`2025-10-21 06:25:30 +00:00` |
| `last_response_at` | string | *date and time when the response data was last updated*in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”example:`2025-10-21 06:25:30 +00:00` |
| **`brand_entities`** | array | *array of brand entities*contains information on brands mentioned in the response |
| `position` | integer | *position in the results* |
| `title` | string | *name of the brand* |
| `category` | string | *category of the brand* |
| `fan_out_queries` | array | *array of fan-out queries*contains related search queries derived from the main query to provide a more comprehensive response |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


#### Top Pages
*Source: [https://docs.dataforseo.com/v3/ai_optimization/llm_mentions/top_pages/live/](https://docs.dataforseo.com/v3/ai_optimization/llm_mentions/top_pages/live/)*
#### Live LLM Mentions Top Pages

Live LLM Mentions Top Pages endpoint provides aggregated LLM mentions metrics grouped by the most frequently mentioned pages for the specified `target`. The results are specific to the selected platform (`google` for Google’s AI Overview or `chat_gpt` for ChatGPT), location and language parameters (see [the List of Locations & Languages](https://docs.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages)).

POSThttps://api.dataforseo.com/v3/ai_optimization/llm_mentions/top_pages/live

Pricing

The cost of the task can be calculated on the [Pricing page](https://dataforseo.com/pricing/ai-optimization/llm-mentions).

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute, each Live LLM Mentions API call can contain only one task.

**Execution time for tasks set with the Live LLM Mentions endpoint is currently up to 120 seconds.**

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| **`target`** | array | *array of objects containing target entities***required field**you can specify **up to 10 entities (objects)** in the `target` fieldone target entity can contain either one `domain` or one `keyword` and related parametersexamples: target array with a domain entity`[{"domain": "en.wikipedia.org", "search_filter": "exclude"}]`target array with a keyword entity`[{"keyword": "bmw", "search_scope": ["question"], "match_type ": "partial_match"}]`target array with multiple entities`[{"domain": "en.wikipedia.org", "search_filter": "exclude"}, {"keyword": "bmw", "match_type ": "partial_match", "search_scope": ["answer"]}]` |
| **`domain_entity`** | object | *domain entity in the target array*example:`{"domain": "en.wikipedia.org", "search_filter": "exclude", "search_scope": ["sources"]}` |
| `domain` | string | *target domain***required field if you don't specify `keyword`**you can specify **up to 63 characters** in the `domain` field;a domain should be specified without `https://` and `www.` |
| `search_filter` | string | *target domain search filter*optional fieldpossible values:`include`, `exclude`default value: `include` |
| `search_scope` | array | *target domain search scope*optional fieldpossible values:`any`, `sources`, `search_results`default value: `any` |
| `include_subdomains` | boolean | *indicates if the subdomains of the target `domain` will be included in the search*optional fieldif set to `true`, the subdomains will be included in the searchdefault value: `false` |
| **`keyword_entity`** | object | *keyword entity in the target array*example:`{"keyword": "bmw", "search_filter": "include", "search_scope": ["question"], "match_type ": "partial_match"}` |
| `keyword` | string | *target keyword***required field if you don't specify `domain`**you can specify **up to 250 characters** in the `keyword` fieldall %## will be decoded (plus character ‘+’ will be decoded to a space character)if you need to use the “%” character for your `keyword`, please specify it as “%25”;if you need to use the “+” character for your `keyword`, please specify it as “%2B”learn more about rules and limitations of `keyword` and `keywords` fields in DataForSEO APIs in this [Help Center article](https://dataforseo.com/help-center/rules-and-limitations-of-keyword-and-keywords-fields-in-dataforseo-apis) |
| `search_filter` | string | *target keyword search filter*optional fieldpossible values:`include`, `exclude`default value: `include` |
| `search_scope` | array | *target keyword search scope*optional fieldpossible values:`any`, `question`, `answer`, `brand_entities`, `fan_out_queries`default value: `any` |
| `match_type` | string | *target keyword match type*optional fieldpossible values:`word_match`, `partial_match``word_match` - full-text search for terms that match the specified seed keyword with additional words included before, after, or within the seed key phrase.`partial_match` - searches for any occurrence of the keyword or its parts within the contentdefault value: `word_match` |
| `location_name` | string | *full name of search location*optional fieldif you use this field, you don't need to specify `location_code`if you don't specify this field, the `location_code` with `2840` value will be used by default;you can receive the list of available locations of the search engine with their `location_name` by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages](https://api.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages)`**Note: `chat_gpt` data is available for `United States` only** |
| `location_code` | integer | *search location code*optional fieldif you use this field, you don't need to specify `location_name`you can receive the list of available locations of the search engine with their `location_code` by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages](https://api.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages)`default value: `2840`**Note: `chat_gpt` data is available for `2840` only** |
| `language_name` | string | *full name of search language*optional fieldif you use this field, you don't need to specify `language_code`;if you don't specify this field, the `language_code` with `en` value will be used by default;you can receive the list of available languages of the search engine with their `language_name` by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages](https://api.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages)`**Note: `chat_gpt` data is available for `English` only** |
| `language_code` | string | *search language code*optional fieldif you use this field, you don't need to specify `language_name`;you can receive the list of available languages of the search engine with their `language_code`_by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages](https://api.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages)`default value: `en`**Note: `chat_gpt` data is available for `en` onlyn** |
| `platform` | string | *target platform*optional fieldpossible values:`chat_gpt`, `google`default value: `google`**Note:** the data returned depends on the selected platform**Note #2:**`chat_gpt` data is available for the `United States` and `English` only |
| `links_scope` | string | *links source scope*optional fieldthis parameter specifies which links will be used to extract pages and aggregation datapossible values: `sources`, `search_results`default value: `sources` |
| `initial_dataset_filters` | array | *array of filter expressions applied before aggregation*optional fieldyou can use this array to filter expressions applied to the raw mentions database before aggregation to limit the rows contributing to the result;**you can add several filters at once (8 filters maximum)**you should set a logical operator `and`, `or` between the conditionsthe following operators are supported:`=`, `<>`, `in`, `not_in`, `like`, `not_like`, `ilike`, `not_ilike`, `match`, `not_match`you can use the `%` operator with `like` and `not_like` to match any string of zero or more charactersexample:`["ai_search_volume",">","1000"]`the full list of possible filters is available [here.](https://docs.dataforseo.com/v3/ai_optimization/llm_mentions/filters)learn more about the initial dataset filters in [this help center article.](https://dataforseo.com/help-center/what-are-the-initial-dataset-filters-and-how-do-they-work) |
| `items_list_limit` | integer | *maximum number of results in the items array*optional fieldyou can use this parameter to limit the number of data objects you receive in the `items` arrayminimum value: `1`maximum value: `10`default value: `5` |
| `internal_list_limit` | integer | *maximum number of elements within internal arrays*optional fieldyou can use this field to limit the number of elements within the following arrays:`sources_domain``search_results_domain`minimum value: `1`maximum value: `10`default value: `5` |
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
| `status_code` | integer | *status code of the task*generated by DataForSEO; can be within the following range: 10000-60000you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| **`total`** | object | *aggregated mentions metrics summary*contains overall aggregated LLM mention metrics across all found top pages, grouped by various dimensions |
| **`location`** | array | *location-based grouping*array of objects containing mention metrics segmented by geographical location |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimension |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to this specific grouping key |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *AI impressions rate of a keyword*deprecated field, the value will be `null` |
| **`language`** | array | *language-based grouping*array of objects containing mention metrics segmented by content language |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimension |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to this specific grouping key |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |
| **`platform`** | array | *platform-based grouping*array of group elements containing mention metrics segmented by AI platform |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimension |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to this specific grouping key |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |
| **`sources_domain`** | array | *found source domains relevant to the target*array of objects containing data on top domains that are cited as sources in LLM responseslearn more about the sources and how to retrieve LLM citation data at our [Help Center](https://dataforseo.com/help-center/how-to-get-llm-citation-data-with-llm-mentions-api) |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimensionin this case the field displays a found domain name |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to the specific domain |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |
| **`search_results_domain`** | array | *found search results domains relevant to the target*array of objects containing data on top domains that appear in search results related to LLM queries |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimensionin this case the field displays a found domain name |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to the specific domain |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |
| **`brand_entities_title`** | array | *data on brand entities relevant to the target*array of objects containing data on brand entity titles that appear in search results related to LLM queries |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimensionin this case the field displays a found brand entity title |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to the specific domain |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |
| **`brand_entities_category`** | array | *data on brand entities relevant to the target*array of objects containing data on brand entity categories that appear in search results related to LLM queries |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimensionin this case the field displays a found brand entity category |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to the specific domain |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |
| **`items`** | array | *individual pages results*array containing detailed mention metrics for each of the found top pages |
| `key` | string | *URL of a found page*the URL of a page found in LLM mentions for the specified target |
| **`location`** | array | *location-based grouping*array of objects containing page mention metrics segmented by geographical location |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimension |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to this specific grouping key |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |
| **`language`** | array | *language-based grouping*array of objects containing page mention metrics segmented by content language |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimension |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to this specific grouping key |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |
| **`platform`** | array | *platform-based grouping*array of group elements containing page mention metrics segmented by AI platform |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimension |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to this specific grouping key |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |
| **`sources_domain`** | array | *source domains relevant to the specific page*array of objects containing data on domains that are cited as sources in LLM responses |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimensionin this case the field displays a found domain name |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to the specific domain |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |
| **`search_results_domain`** | array | *search results domains relevant to the specific page*array of objects containing data on domains that appear in search results related to LLM queries |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimensionin this case the field displays a found domain name |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to the specific domain |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |
| **`brand_entities_title`** | array | *data on brand entities relevant to the target*array of objects containing data on brand entity titles that appear in search results related to LLM queries |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimensionin this case the field displays a found brand entity title |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to the specific domain |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |
| **`brand_entities_category`** | array | *data on brand entities relevant to the target*array of objects containing data on brand entity categories that appear in search results related to LLM queries |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimensionin this case the field displays a found brand entity category |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to the specific domain |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


#### Top Domains
*Source: [https://docs.dataforseo.com/v3/ai_optimization/llm_mentions/top_domains/live/](https://docs.dataforseo.com/v3/ai_optimization/llm_mentions/top_domains/live/)*
#### Live LLM Mentions Top Domains

Live LLM Mentions Top Domains endpoint provides aggregated LLM mentions metrics grouped by the most frequently mentioned domains for the specified `target`. The results are specific to the selected platform (`google` for Google’s AI Overview or `chat_gpt` for ChatGPT), location and language parameters (see [the List of Locations & Languages](https://docs.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages)).

POSThttps://api.dataforseo.com/v3/ai_optimization/llm_mentions/top_domains/live

Pricing

The cost of the task can be calculated on the [Pricing page](https://dataforseo.com/pricing/ai-optimization/llm-mentions).

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute, each Live LLM Mentions API call can contain only one task.

**Execution time for tasks set with the Live LLM Mentions endpoint is currently up to 120 seconds.**

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| **`target`** | array | *array of objects containing target entities***required field**you can specify **up to 10 entities (objects)** in the `target` fieldone target entity can contain either one `domain` or one `keyword` and related parametersexamples: target array with a domain entity`[{"domain": "en.wikipedia.org", "search_filter": "exclude"}]`target array with a keyword entity`[{"keyword": "bmw", "search_scope": ["question"], "match_type ": "partial_match"}]`target array with multiple entities`[{"domain": "en.wikipedia.org", "search_filter": "exclude"}, {"keyword": "bmw", "match_type ": "partial_match", "search_scope": ["answer"]}]` |
| **`domain_entity`** | object | *domain entity in the target array*example:`{"domain": "en.wikipedia.org", "search_filter": "exclude", "search_scope": ["sources"]}` |
| `domain` | string | *target domain***required field if you don't specify `keyword`**you can specify **up to 63 characters** in the `domain` field;a domain should be specified without `https://` and `www.` |
| `search_filter` | string | *target domain search filter*optional fieldpossible values:`include`, `exclude`default value: `include` |
| `search_scope` | array | *target domain search scope*optional fieldpossible values:`any`, `sources`, `search_results`default value: `any` |
| `include_subdomains` | boolean | *indicates if the subdomains of the target `domain` will be included in the search*optional fieldif set to `true`, the subdomains will be included in the searchdefault value: `false` |
| **`keyword_entity`** | object | *keyword entity in the target array*example:`{"keyword": "bmw", "search_filter": "include", "search_scope": ["question"], "match_type ": "partial_match"}` |
| `keyword` | string | *target keyword***required field if you don't specify `domain`**you can specify **up to 250 characters** in the `keyword` fieldall %## will be decoded (plus character ‘+’ will be decoded to a space character)if you need to use the “%” character for your `keyword`, please specify it as “%25”;if you need to use the “+” character for your `keyword`, please specify it as “%2B”learn more about rules and limitations of `keyword` and `keywords` fields in DataForSEO APIs in this [Help Center article](https://dataforseo.com/help-center/rules-and-limitations-of-keyword-and-keywords-fields-in-dataforseo-apis) |
| `search_filter` | string | *target keyword search filter*optional fieldpossible values:`include`, `exclude`default value: `include` |
| `search_scope` | array | *target keyword search scope*optional fieldpossible values:`any`, `question`, `answer`, `brand_entities`, `fan_out_queries`default value: `any` |
| `match_type` | string | *target keyword match type*optional fieldpossible values:`word_match`, `partial_match``word_match` - full-text search for terms that match the specified seed keyword with additional words included before, after, or within the seed key phrase.`partial_match` - searches for any occurrence of the keyword or its parts within the contentdefault value: `word_match` |
| `location_name` | string | *full name of search location*optional fieldif you use this field, you don't need to specify `location_code`if you don't specify this field, the `location_code` with `2840` value will be used by default;you can receive the list of available locations of the search engine with their `location_name` by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages](https://api.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages)`**Note: `chat_gpt` data is available for `United States` only** |
| `location_code` | integer | *search location code*optional fieldif you use this field, you don't need to specify `location_name`you can receive the list of available locations of the search engine with their `location_code` by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages](https://api.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages)`default value: `2840`**Note: `chat_gpt` data is available for `2840` only** |
| `language_name` | string | *full name of search language*optional fieldif you use this field, you don't need to specify `language_code`;if you don't specify this field, the `language_code` with `en` value will be used by default;you can receive the list of available languages of the search engine with their `language_name` by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages](https://api.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages)`**Note: `chat_gpt` data is available for `English` only** |
| `language_code` | string | *search language code*optional fieldif you use this field, you don't need to specify `language_name`;you can receive the list of available languages of the search engine with their `language_code`_by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages](https://api.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages)`default value: `en`**Note: `chat_gpt` data is available for `en` onlyn** |
| `platform` | string | *target platform*optional fieldpossible values:`chat_gpt`, `google`default value: `google`**Note:** the data returned depends on the selected platform**Note #2:**`chat_gpt` data is available for the `United States` and `English` only |
| `links_scope` | string | *links source scope*optional fieldthis parameter specifies which links will be used to extract domains and aggregation datapossible values: `sources`, `search_results`default value: `sources` |
| `initial_dataset_filters` | array | *array of filter expressions applied before aggregation*optional fieldyou can use this array to filter expressions applied to the raw mentions database before aggregation to limit the rows contributing to the result;**you can add several filters at once (8 filters maximum)**you should set a logical operator `and`, `or` between the conditionsthe following operators are supported:`=`, `<>`, `in`, `not_in`, `like`, `not_like`, `ilike`, `not_ilike`, `match`, `not_match`you can use the `%` operator with `like` and `not_like` to match any string of zero or more charactersexample:`["ai_search_volume",">","1000"]`the full list of possible filters is available [here.](https://docs.dataforseo.com/v3/ai_optimization/llm_mentions/filters)learn more about the initial dataset filters in [this help center article.](https://dataforseo.com/help-center/what-are-the-initial-dataset-filters-and-how-do-they-work) |
| `items_list_limit` | integer | *maximum number of results in the items array*optional fieldyou can use this parameter to limit the number of data objects you receive in the `items` arrayminimum value: `1`maximum value: `10`default value: `5` |
| `internal_list_limit` | integer | *maximum number of elements within internal arrays*optional fieldyou can use this field to limit the number of elements within the following arrays:`sources_domain``search_results_domain`minimum value: `1`maximum value: `10`default value: `5` |
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
| `status_code` | integer | *status code of the task*generated by DataForSEO; can be within the following range: 10000-60000you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| **`total`** | object | *aggregated mentions metrics summary*contains overall aggregated LLM mention metrics across all found domains, grouped by various dimensions |
| **`location`** | array | *location-based grouping*array of objects containing mention metrics segmented by geographical location |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimension |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to this specific grouping key |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |
| **`language`** | array | *language-based grouping*array of objects containing mention metrics segmented by content language |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimension |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to this specific grouping key |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |
| **`platform`** | array | *platform-based grouping*array of group elements containing mention metrics segmented by AI platform |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimension |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to this specific grouping key |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |
| **`sources_domain`** | array | *found top source domains relevant to the target*array of objects containing data on top domains that are cited as sources in LLM responseslearn more about the sources and how to retrieve LLM citation data at our [Help Center](https://dataforseo.com/help-center/how-to-get-llm-citation-data-with-llm-mentions-api) |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimensionin this case the field displays a found domain name |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to the specific domain |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |
| **`search_results_domain`** | array | *found top search results domains relevant to the target*array of objects containing data on top domains that appear in search results related to LLM queries |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimensionin this case the field displays a found domain name |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to the specific domain |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |
| **`brand_entities_title`** | array | *data on brand entities relevant to the target*array of objects containing data on brand entity titles that appear in search results related to LLM queries |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimensionin this case the field displays a found brand entity title |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to the specific domain |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |
| **`brand_entities_category`** | array | *data on brand entities relevant to the target*array of objects containing data on brand entity categories that appear in search results related to LLM queries |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimensionin this case the field displays a found brand entity category |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to the specific domain |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |
| **`items`** | array | *individual domain results*array containing detailed mention metrics for each of the found top domains |
| `key` | string | *domain name*the domain name of the website found in LLM mentions for the specified target |
| **`location`** | array | *location-based grouping*array of objects containing domain mention metrics segmented by geographical location |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimension |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to this specific grouping key |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |
| **`language`** | array | *language-based grouping*array of objects containing domain mention metrics segmented by content language |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimension |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to this specific grouping key |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |
| **`platform`** | array | *platform-based grouping*array of group elements containing domain mention metrics segmented by AI platform |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimension |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to this specific grouping key |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |
| **`sources_domain`** | array | *source domains relevant to the specific top domain*array of objects containing data on domains that are cited as sources in LLM responseslearn more about the sources and how to retrieve LLM citation data at our [Help Center](https://dataforseo.com/help-center/how-to-get-llm-citation-data-with-llm-mentions-api) |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimensionin this case the field displays a found domain name |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to the specific domain |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |
| **`search_results_domain`** | array | *search results domains relevant to the specific top domain*array of objects containing data on domains that appear in search results related to LLM queries |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimensionin this case the field displays a found domain name |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to the specific domain |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |
| **`brand_entities_title`** | array | *data on brand entities relevant to the target*array of objects containing data on brand entity titles that appear in search results related to LLM queries |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimensionin this case the field displays a found brand entity title |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to the specific domain |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |
| **`brand_entities_category`** | array | *data on brand entities relevant to the target*array of objects containing data on brand entity categories that appear in search results related to LLM queries |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimensionin this case the field displays a found brand entity category |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to the specific domain |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


#### Aggregated Metrics
*Source: [https://docs.dataforseo.com/v3/ai_optimization/llm_mentions/aggregated_metrics/live/](https://docs.dataforseo.com/v3/ai_optimization/llm_mentions/aggregated_metrics/live/)*
#### Live LLM Mentions Aggregated Metrics

Live LLM Mentions endpoint provides aggregated metrics for mentions of the keywords or domains specified in the `target` array of the request. The results are specific to the selected platform (`google` for Google’s AI Overview or `chat_gpt` for ChatGPT), location and language parameters (see [the List of Locations & Languages](https://docs.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages)).

POSThttps://api.dataforseo.com/v3/ai_optimization/llm_mentions/aggregated_metrics/live

Pricing

The cost of the task can be calculated on the [Pricing page](https://dataforseo.com/pricing/ai-optimization/llm-mentions).

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute, each Live LLM Mentions API call can contain only one task.

**Execution time for tasks set with the Live LLM Mentions endpoint is currently up to 120 seconds.**

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| **`target`** | array | *array of objects containing target entities***required field**you can specify **up to 10 entities (objects)** in the `target` fieldone target entity can contain either one `domain` or one `keyword` and related parametersexamples: target array with a domain entity`[{"domain": "en.wikipedia.org", "search_filter": "exclude"}]`target array with a keyword entity`[{"keyword": "bmw", "search_scope": ["question"], "match_type ": "partial_match"}]`target array with multiple entities`[{"domain": "en.wikipedia.org", "search_filter": "exclude"}, {"keyword": "bmw", "match_type ": "partial_match", "search_scope": ["answer"]}]` |
| **`domain_entity`** | object | *domain entity in the target array*example:`{"domain": "en.wikipedia.org", "search_filter": "exclude", "search_scope": ["sources"]}` |
| `domain` | string | *target domain***required field if you don't specify `keyword`**you can specify **up to 63 characters** in the `domain` field;a domain should be specified without `https://` and `www.` |
| `search_filter` | string | *target domain search filter*optional fieldpossible values:`include`, `exclude`default value: `include` |
| `search_scope` | array | *target domain search scope*optional fieldpossible values:`any`, `sources`, `search_results`default value: `any` |
| `include_subdomains` | boolean | *indicates if the subdomains of the target `domain` will be included in the search*optional fieldif set to `true`, the subdomains will be included in the searchdefault value: `false` |
| **`keyword_entity`** | object | *keyword entity in the target array*example:`{"keyword": "bmw", "search_filter": "include", "search_scope": ["question"], "match_type ": "partial_match"}` |
| `keyword` | string | *target keyword***required field if you don't specify `domain`**you can specify **up to 250 characters** in the `keyword` fieldall %## will be decoded (plus character ‘+’ will be decoded to a space character)if you need to use the “%” character for your `keyword`, please specify it as “%25”;if you need to use the “+” character for your `keyword`, please specify it as “%2B”learn more about rules and limitations of `keyword` and `keywords` fields in DataForSEO APIs in this [Help Center article](https://dataforseo.com/help-center/rules-and-limitations-of-keyword-and-keywords-fields-in-dataforseo-apis) |
| `search_filter` | string | *target keyword search filter*optional fieldpossible values:`include`, `exclude`default value: `include` |
| `search_scope` | array | *target keyword search scope*optional fieldpossible values:`any`, `question`, `answer`, `brand_entities`, `fan_out_queries`default value: `any` |
| `match_type` | string | *target keyword match type*optional fieldword_match - full-text search for terms that match the specified seed keyword with additional words included before, after, or within the key phrase (e.g., search for “light” will return results with “light bulb”, “light switch”);partial_match - substring search that finds all instances containing the specified sequence of characters, even if it appears inside a longer word (e.g., search for “light” will return results with “lighting”, “highlight”);possible values:`word_match`, `partial_match`default value: `word_match` |
| `location_name` | string | *full name of search location*optional fieldif you use this field, you don't need to specify `location_code`if you don't specify this field, the `location_code` with `2840` value will be used by default;you can receive the list of available locations of the search engine with their `location_name` by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages](https://api.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages)`**Note: `chat_gpt` data is available for `United States` only** |
| `location_code` | integer | *search location code*optional fieldif you use this field, you don't need to specify `location_name`you can receive the list of available locations of the search engine with their `location_code` by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages](https://api.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages)`default value: `2840`**Note: `chat_gpt` data is available for `2840` only** |
| `language_name` | string | *full name of search language*optional fieldif you use this field, you don't need to specify `language_code`;if you don't specify this field, the `language_code` with `en` value will be used by default;you can receive the list of available languages of the search engine with their `language_name` by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages](https://api.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages)`**Note: `chat_gpt` data is available for `English` only** |
| `language_code` | string | *search language code*optional fieldif you use this field, you don't need to specify `language_name`;you can receive the list of available languages of the search engine with their `language_code`_by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages](https://api.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages)`default value: `en`**Note: `chat_gpt` data is available for `en` onlyn** |
| `platform` | string | *target platform*optional fieldpossible values:`chat_gpt`, `google`default value: `google`**Note:** the data returned depends on the selected platform**Note #2:**`chat_gpt` data is available for the `United States` and `English` only |
| `initial_dataset_filters` | array | *array of filter expressions applied before aggregation*optional fieldyou can use this array to filter expressions applied to the raw mentions database before aggregation to limit the rows contributing to the result;**you can add several filters at once (8 filters maximum)**you should set a logical operator `and`, `or` between the conditionsthe following operators are supported:`=`, `<>`, `in`, `not_in`, `like`, `not_like`, `ilike`, `not_ilike`, `match`, `not_match`you can use the `%` operator with `like` and `not_like` to match any string of zero or more charactersexample:`["ai_search_volume",">","1000"]`the full list of possible filters is available [here.](https://docs.dataforseo.com/v3/ai_optimization/llm_mentions/filters)learn more about the initial dataset filters in [this help center article.](https://dataforseo.com/help-center/what-are-the-initial-dataset-filters-and-how-do-they-work) |
| `internal_list_limit` | integer | *maximum number of elements within internal arrays*optional fieldyou can use this field to limit the number of elements within the following arrays:`sources_domain``search_results_domain`minimum value: `1`maximum value: `20`default value: `10` |
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
| `status_code` | integer | *status code of the task*generated by DataForSEO; can be within the following range: 10000-60000you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| **`total`** | object | *aggregated mentions metrics summary*contains overall aggregated LLM mention metrics across all found domains, grouped by various dimensions |
| **`location`** | array | *location-based grouping*array of objects containing mention metrics segmented by geographical location |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimension |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to this specific grouping key |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |
| **`language`** | array | *language-based grouping*array of objects containing mention metrics segmented by content language |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimension |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to this specific grouping key |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |
| **`platform`** | array | *platform-based grouping*array of group elements containing mention metrics segmented by AI platform |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimension |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to this specific grouping key |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |
| **`sources_domain`** | array | *found top source domains relevant to the target*array of objects containing data on top domains that are cited as sources in LLM responseslearn more about the sources and how to retrieve LLM citation data at our [Help Center](https://dataforseo.com/help-center/how-to-get-llm-citation-data-with-llm-mentions-api) |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimensionin this case the field displays a found domain name |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to the specific domain |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |
| **`search_results_domain`** | array | *found top search results domains relevant to the target*array of objects containing data on top domains that appear in search results related to LLM queries |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimensionin this case the field displays a found domain name |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to the specific domain |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |
| **`brand_entities_title`** | array | *data on brand entities relevant to the target*array of objects containing data on brand entity titles that appear in search results related to LLM queries |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimensionin this case the field displays a found brand entity title |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to the specific domain |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |
| **`brand_entities_category`** | array | *data on brand entities relevant to the target*array of objects containing data on brand entity categories that appear in search results related to LLM queries |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimensionin this case the field displays a found brand entity category |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to the specific domain |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |
| `items` | array | *individual pages results*array containing detailed mention metrics for each of the found top pagesin this case, equals `null` |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


#### Cross Aggregated Metrics
*Source: [https://docs.dataforseo.com/v3/ai_optimization/llm_mentions/cross_aggregated_metrics/live/](https://docs.dataforseo.com/v3/ai_optimization/llm_mentions/cross_aggregated_metrics/live/)*
#### Live LLM Mentions Cross Aggregated Metrics

Live LLM Mentions endpoint provides aggregated metrics grouped by custom keys for mentions of the keywords or domains specified in the `target` array of the request. Each item in the results array corresponds to the specified target. The results are specific to the selected platform (`google` for Google’s AI Overview or `chat_gpt` for ChatGPT), location and language parameters (see [the List of Locations & Languages](https://docs.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages)).

POSThttps://api.dataforseo.com/v3/ai_optimization/llm_mentions/cross_aggregated_metrics/live

Pricing

The cost of the task can be calculated on the [Pricing page](https://dataforseo.com/pricing/ai-optimization/llm-mentions).

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute, each Live LLM Mentions API call can contain only one task.

**Execution time for tasks set with the Live LLM Mentions endpoint is currently up to 120 seconds.**

Below you will find a detailed description of the fields you can use for setting a task.

| Field name | Type | Description |
| --- | --- | --- |
| **`targets`** | array | *array of objects containing target entities with aggregation keys***required field**you can specify **up to 10, but not less than 2** `target` sets of parameters, each with its `aggregation_key`;example of a `targets` array with multiple entities:`[{"aggregation_key":"bmw","target":[{"domain":"en.wikipedia.org","search_filter":"exclude"},{"keyword":"m5","match_type":"partial_match","search_scope":["answer"]}]},{"aggregation_key":"mercedes","target":[{"domain":"www.mercedes-benz.com","search_filter":"exclude"},{"keyword":"GLC","match_type":"word_match"}]}]` |
| `aggregation_key` | string | *aggregation key for grouping the results***required field**groups results for comparison and serves as a label for the group;you can specify **up to 250 characters** in the `aggregation_key` field |
| `target` | array | *array of objects containing target entities***required field**a single `target` can contain up to 10 `domain` and/or `keyword` entities |
| **`domain_entity`** | object | *domain entity in the target array*example:`{"domain": "en.wikipedia.org", "search_filter": "exclude", "search_scope": ["sources"]}` |
| `domain` | string | *target domain***required field if you don't specify a `keyword`**you can specify **up to 63 characters** in the `domain` field;a domain should be specified without `https://` and `www.` |
| `search_filter` | string | *target domain search filter*optional fieldpossible values:`include`, `exclude`default value: `include` |
| `search_scope` | array | *target domain search scope*optional fieldpossible values:`any`, `sources`, `search_results`default value: `any` |
| `include_subdomains` | boolean | *indicates if the subdomains of the target `domain` will be included in the search*optional fieldif set to `true`, the subdomains will be included in the searchdefault value: `false` |
| **`keyword_entity`** | object | *keyword entity in the target array*example:`{"keyword": "bmw", "search_filter": "include", "search_scope": ["question"], "match_type ": "partial_match"}` |
| `keyword` | string | *target keyword***required field if you don't specify a `domain`**you can specify **up to 250 characters** in the `keyword` fieldall %## will be decoded (plus character ‘+’ will be decoded to a space character)if you need to use the “%” character for your `keyword`, please specify it as “%25”;if you need to use the “+” character for your `keyword`, please specify it as “%2B”learn more about rules and limitations of `keyword` and `keywords` fields in DataForSEO APIs in this [Help Center article](https://dataforseo.com/help-center/rules-and-limitations-of-keyword-and-keywords-fields-in-dataforseo-apis) |
| `search_filter` | string | *target keyword search filter*optional fieldpossible values:`include`, `exclude`default value: `include` |
| `search_scope` | array | *target keyword search scope*optional fieldpossible values:`any`, `question`, `answer`, `brand_entities`, `fan_out_queries`default value: `any` |
| `match_type` | string | *target keyword match type*defines how the specified keyword is matchedoptional fieldpossible values:`word_match` - full-text search for terms that match the specified seed keyword with additional words included before, after, or within the key phrase (e.g., search for "light" will return results with "light bulb", "light switch");`partial_match` - substring search that finds all instances containing the specified sequence of characters, even if it appears inside a longer word (e.g., search for "light" will return results with "lighting", "highlight");default value: `word_match` |
| `location_name` | string | *full name of search location*optional fieldif you use this field, you don't need to specify `location_code`if you don't specify this field, the `location_code` with `2840` value will be used by default;you can receive the list of available locations of the search engine with their `location_name` by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages](https://api.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages)`**Note: `chat_gpt` data is available for `United States` only** |
| `location_code` | integer | *search location code*optional fieldif you use this field, you don't need to specify `location_name`you can receive the list of available locations of the search engine with their `location_code` by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages](https://api.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages)`default value: `2840`**Note: `chat_gpt` data is available for `2840` only** |
| `language_name` | string | *full name of search language*optional fieldif you use this field, you don't need to specify `language_code`;if you don't specify this field, the `language_code` with `en` value will be used by default;you can receive the list of available languages of the search engine with their `language_name` by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages](https://api.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages)`**Note: `chat_gpt` data is available for `English` only** |
| `language_code` | string | *search language code*optional fieldif you use this field, you don't need to specify `language_name`;you can receive the list of available languages of the search engine with their `language_code`_by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages](https://api.dataforseo.com/v3/ai_optimization/llm_mentions/locations_and_languages)`default value: `en`**Note: `chat_gpt` data is available for `en` onlyn** |
| `platform` | string | *target platform*optional fieldpossible values:`chat_gpt`, `google`default value: `google`**Note:** the data returned depends on the selected platform**Note #2:**`chat_gpt` data is available for the `United States` and `English` only |
| `initial_dataset_filters` | array | *array of filter expressions applied before aggregation*optional fieldyou can use this array to filter expressions applied to the raw mentions database before aggregation to limit the rows contributing to the result;**you can add several filters at once (8 filters maximum)**you should set a logical operator `and`, `or` between the conditionsthe following operators are supported:`=`, `<>`, `in`, `not_in`, `like`, `not_like`, `ilike`, `not_ilike`, `match`, `not_match`you can use the `%` operator with `like` and `not_like` to match any string of zero or more charactersexample:`["ai_search_volume",">","1000"]`the full list of possible filters is available [here.](https://docs.dataforseo.com/v3/ai_optimization/llm_mentions/filters)learn more about the initial dataset filters in [this help center article.](https://dataforseo.com/help-center/what-are-the-initial-dataset-filters-and-how-do-they-work) |
| `internal_list_limit` | integer | *maximum number of elements within internal arrays*optional fieldyou can use this field to limit the number of elements within the following arrays:`sources_domain``search_results_domain`minimum value: `1`maximum value: `10`default value: `5` |
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
| `status_code` | integer | *status code of the task*generated by DataForSEO; can be within the following range: 10000-60000you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| **`total`** | object | *aggregated mentions metrics summary*contains overall aggregated LLM mention metrics across all found domains, grouped by various dimensions |
| **`location`** | array | *location-based grouping*array of objects containing mention metrics segmented by geographical location |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimension |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to this specific grouping key |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |
| **`language`** | array | *language-based grouping*array of objects containing mention metrics segmented by content language |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimension |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to this specific grouping key |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |
| **`platform`** | array | *platform-based grouping*array of group elements containing mention metrics segmented by AI platform |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimension |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to this specific grouping key |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |
| **`sources_domain`** | array | *found top source domains relevant to the target*array of objects containing data on top domains that are cited as sources in LLM responseslearn more about the sources and how to retrieve LLM citation data at our [Help Center](https://dataforseo.com/help-center/how-to-get-llm-citation-data-with-llm-mentions-api) |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimensionin this case the field displays a found domain name |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to the specific domain |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |
| **`search_results_domain`** | array | *found top search results domains relevant to the target*array of objects containing data on top domains that appear in search results related to LLM queries |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimensionin this case the field displays a found domain name |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to the specific domain |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |
| **`brand_entities_title`** | array | *data on brand entities relevant to the target*array of objects containing data on brand entity titles that appear in search results related to LLM queries |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimensionin this case the field displays a found brand entity title |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to the specific domain |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |
| **`brand_entities_category`** | array | *data on brand entities relevant to the target*array of objects containing data on brand entity categories that appear in search results related to LLM queries |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimensionin this case the field displays a found brand entity category |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to the specific domain |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |
| **`items`** | array | *contains relevant mentions data* |
| `key` | string | *aggregation key received in a POST array* |
| **`location`** | array | *location-based grouping*array of objects containing mention metrics segmented by geographical location |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimension |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to this specific grouping key |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |
| **`language`** | array | *language-based grouping*array of objects containing mention metrics segmented by content language |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimension |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to this specific grouping key |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |
| **`platform`** | array | *platform-based grouping*array of group elements containing mention metrics segmented by AI platform |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimension |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to this specific grouping key |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |
| **`sources_domain`** | array | *found top source domains relevant to the target*array of objects containing data on top domains that are cited as sources in LLM responseslearn more about the sources and how to retrieve LLM citation data at our [Help Center](https://dataforseo.com/help-center/how-to-get-llm-citation-data-with-llm-mentions-api) |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimensionin this case the field displays a found domain name |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to the specific domain |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |
| **`search_results_domain`** | array | *found top search results domains relevant to the target*array of objects containing data on top domains that appear in search results related to LLM queries |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimensionin this case the field displays a found domain name |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to the specific domain |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |
| **`brand_entities_title`** | array | *data on brand entities relevant to the target*array of objects containing data on brand entity titles that appear in search results related to LLM queries |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimensionin this case the field displays a found brand entity title |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to the specific domain |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |
| **`brand_entities_category`** | array | *data on brand entities relevant to the target*array of objects containing data on brand entity categories that appear in search results related to LLM queries |
| `type` | string | *type of the element = '**group_element**'* |
| `key` | string | *grouping identifier*the specific identifier for the grouping dimensionin this case the field displays a found brand entity category |
| `mentions` | integer | *total LLM mentions count*the number of times the target keyword or domain were mentioned in relation to the specific domain |
| `ai_search_volume` | integer | *current AI search volume rate of a keyword*learn more about this metric [here](https://dataforseo.com/help-center/how-the-ai-search-volume-metric-works-in-llm-mentions) |
| `impressions` | integer | *current AI impressions rate of a keyword*deprecated field, the value will be `null` |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Overview
*Source: [https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_responses/overview/](https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_responses/overview/)*
### ChatGPT LLM Responses: Overview

This API allows you to generate and retrieve structured ChatGPT responses

LLM Responses ChatGPT API enables generation of structured responses from ChatGPT, based on your specified input parameters. You can use this API to discover how ChatGPT responds to queries about your brand, product, competitors, or any other target keywords and topics.

The endpoints of this API include:

• [LLM Responses ChatGPT endpoint](https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_responses/live/) retrieves structured responses from a specific ChatGPT AI model, based on your input parameters.

• [LLM Responses ChatGPT Models endpoint](https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_responses/models/) provides a list of available ChatGPT AI models you can use with LLM Responses ChatGPT endpoint.

To find answers on common questions about AI Optimization API and find guidance on most efficient use, [visit our Help Center.](https://dataforseo.com/help-center/category/ai-optimization-api)

##### Methods

The cost of using LLM Responses ChatGPT API depends on the selected method and priority of task execution. Available methods and priorities are described below.

DataForSEO has two main methods to deliver the results: Standard and Live.

If your system requires delivering instant results, **the Live method** is the best solution for you. Unlike the Standard method, this method doesn’t require making separate POST and GET requests to the corresponding endpoints.

If you don’t need to receive data in real-time, you can use **the Standard method** of data retrieval. This method requires making separate POST and GET requests, but it’s more affordable. Using this method, you can retrieve the results after our system collects them.

Alternatively, you can specify `pingback_url` or `postback_url` when setting a task, and we will notify you on completion of tasks or send them to you respectively.

If you need to set several tasks, you can receive the list of id for all completed tasks using **‘Tasks Ready’** endpoint, and then collect the results of each separate task using **‘Task GET’** endpoint.

You can send up to 2000 API calls per minute. Contact us if you would like to raise the limit. Note that the maximum number of Live requests that can be sent simultaneously **is limited to 30** per account for each platform in the LLM Responses.

Execution time for tasks set using [the Live method](https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_responses/live/) is currently **up to 120 seconds**. Tasks set using [the Standard method](https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_responses/task_post/) **may take up to 72 hours to complete**.

##### Cost

The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/ai-optimization/llm-responses) page. You can check your spending in your [account dashboard](https://app.dataforseo.com/api-access) or by making a separate call to [the User Data endpoint](https://docs.dataforseo.com/v3/appendix/user_data/?php)

You can test LLM Responses ChatGPT API for free using DataForSEO [Sandbox.](https://docs.dataforseo.com/v3/appendix/sandbox/)

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

---


##### Models
*Source: [https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_responses/models/](https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_responses/models/)*
#### ChatGPT LLM Responses Models List

Pricing

Your account will not be charged for using this API

GEThttps://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_responses/models

You will receive the list of available Chat GPT AI models by calling this API.
 
As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *general informational message*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total tasks cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier***unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*generated by DataForSEO; can be within the following range: 10000-60000you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the parameters passed in the URL of the GET request* |
| **`result`** | array | *array of results* |
| `model_name` | string | *name of the AI model* |
| `reasoning` | boolean | *indicates if the AI model supports reasoning* |
| `web_search_supported` | boolean | *web search support for the AI model*if `true`, the `web_search` parameter can be set with the AI model |
| `task_post_supported` | boolean | *indicates if Standard (POST-GET) data retrieval is supported*if `true`, you can use the [Standard (POST-GET)](https://dataforseo.com/help-center/live-vs-standard-method) data retrieval method with the AI model |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Task POST
*Source: [https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_responses/task_post/](https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_responses/task_post/)*
#### Setting ChatGPT LLM Responses

ChatGPT LLM Responses endpoint allows you to retrieve structured responses from a specific ChatGPT model, based on the input parameters.

This is the Standard method of data retrieval. If you don’t need to receive data in real-time, this method is the best option for you. Set a task and retrieve the results when our system collects them. Execution time depends on the system workload.

If your system requires delivering instant results, [the Live method](https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_responses/live/) will be a better solution. This method doesn’t require making separate POST and GET requests to the corresponding endpoints.

Note that this endpoint requires making an automatic prepayment of $0.01 to execute the task. If the cost charged by the LLM is less than $0.01, the difference will be refunded to your account balance.

POSThttps://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_responses/task_post

Pricing

Your account will be charged only for setting a task.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/ai-optimization/llm-responses) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). Task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute, with each POST call containing no more than 100 tasks. If your POST call contains over 100 tasks, the tasks over this limit will return the `40006` error.

Tasks using the Standard method **may take up to 72 hours to complete**. If the task is not completed within this time, it is marked as failed, and the $0.01 advance is refunded. It is also important to note that if your account balance is negative, you will not receive the results even if the task is completed successfully.

You can also retrieve the results of completed tasks using the unique task identifier `id`. Alternatively, we can send them to you as soon as they are ready if you specify the `postback_url` or `pingback_url` when setting a task. Note that if your server doesn’t respond within 10 seconds, the connection will be aborted by timeout, and the task will be transferred to the [tasks_ready](https://docs.dataforseo.com/v3/keywords_data/google_ads/search_volume/tasks_ready/?php) list. The error code and message depend on your server’s configuration.

See [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) to learn more about using pingbacks and postbacks with DataForSEO APIs.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `user_prompt` | string | *prompt for the AI model***required field**the question or task you want to send to the AI model;you can specify **up to 500 characters** in the `user_prompt` field |
| `model_name` | string | *name of the AI model***required field**`model_name`consists of the actual model name and version name;if the basic model name is specified, its latest version will be set by default;for example, if `gpt-4.1` is specified, the `gpt-4.1-2025-04-14` will be set as `model_name` automatically;you can receive the list of available LLM models by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_responses/models](https://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_responses/models)` |
| `max_output_tokens` | integer | *maximum number of tokens in the AI response*optional fieldminimum value for reasoning models (e.g., `reasoning` is `true` in the [Models endpoint](https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_responses/models/)): `1024`;minimum value for non-reasoning models: `16`;maximum value: `4096`;default value: `2048` |
| `temperature` | float | *randomness of the AI response*optional fieldhigher values make output more diverse; lower values make output more focused;minimum value: `0`maximum value: `2`default value: `0.94`**Note:** not supported in reasoning models |
| `top_p` | float | *diversity of the AI response*optional field controls diversity of the response by limiting token selection;minimum value: `0`maximum value: `1` default value: `0.92`**Note:** `top_p` cannot be used together with `temperature` in the same request |
| `web_search` | boolean | *enable web search*optional fieldwhen enabled, the AI model can access and cite current web information;default value: `false`;**Note:** refer to the [Models endpoint](https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_responses/models/) for a list of models that support `web_search`; |
| `force_web_search` | boolean | *force AI agent to use web search*optional fieldto enable this parameter, `web_search` must also be enabled;when enabled, the AI model is forced to access and cite current web information;default value: `false`;**Note:** even if the parameter is set to `true`, there is no guarantee web sources will be cited in the response **Note #2:** not supported in reasoning models |
| `web_search_country_iso_code` | string | *ISO country code of the location*optional fieldto enable this parameter, `web_search` must also be enabled;when enabled, the AI model will search the web from the country you specify;**Note:** not supported in `o3-mini`, `o1-pro`, `o1` models |
| `web_search_city` | string | *city name of the location*optional field**Note:** not supported in `o3-mini`, `o1-pro`, `o1` models |
| `system_message` | string | *instructions for the AI behaviour*optional fielddefines the AI's role, tone, or specific behavior;you can specify **up to 500 characters** in the `system_message` field |
| `message_chain` | array | *conversation history*optional fieldarray of message objects representing previous conversation turns;each object must contain `role` and `message` parameters:`role` string with either `user` or `ai` role;`message` string with message content (max 500 characters);you can specify ** the maximum of 10 message objects** in the array;example:`"message_chain": [{"role":"user","message":"Hello, what’s up?"},{"role":"ai","message":"Hello! I’m doing well, thank you. How can I assist you today?"}]` |
| `postback_url` | string | *URL for sending task results*optional fieldonce the task is completed, we will send a POST request with its results compressed in the `gzip` format to the `postback_url` you specifiedyou can use the ‘$id’ string as a `$id` variable and ‘$tag’ as urlencoded `$tag` variable. We will set the necessary values before sending the request.example:`[http://your-server.com/postbackscript?id=$id](http://your-server.com/postbackscript?id=$id)``[http://your-server.com/postbackscript?id=$id&tag=$tag](http://your-server.com/postbackscript?id=$id&tag=$tag)`**Note:** special character in `postback_url` will be urlencoded;i.a., the `#` character will be encoded into `%23`learn more on our [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) |
| `pingback_url` | string | *notification URL of a completed task*optional fieldwhen a task is completed we will notify you by GET request sent to the URL you have specifiedyou can use the ‘$id’ string as a `$id` variable and ‘$tag’ as urlencoded `$tag` variable. We will set the necessary values before sending the requestexample:`[http://your-server.com/pingscript?id=$id](http://your-server.com/pingscript?id=$id)``[http://your-server.com/pingscript?id=$id&tag=$tag](http://your-server.com/pingscript?id=$id&tag=$tag)`**Note:** special character in `pingback_url` will be urlencoded;i.a., the `#` character will be encoded into `%23`learn more on our [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) |
| `tag` | string | *user-defined task identifier*optional field*the character limit is 255*you can use this parameter to identify the task and match it with the resultyou will find the specified `tag` value in the `data` array of the response |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)<br>**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total tasks cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`**array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *unique task identifier in our system*<br>**unique task identifier in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task *<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| ** `result`** | array | *array of results*<br>in this case, the value will be `null` |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Tasks Ready
*Source: [https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_responses/tasks_ready/](https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_responses/tasks_ready/)*
#### Get ChatGPT LLM Responses Completed Task

This endpoint is designed to provide you with a list of completed tasks, which haven’t been collected yet. If you use the Standard method without specifying the `postback_url`, you can receive the list of `id` for all completed tasks using this endpoint. Then, you can collect the results using the **‘Task GET’** endpoint.

Learn more about task completion and obtaining a list of completed tasks in [this help center article.](https://dataforseo.com/help-center/completed-tasks)

Tasks using the Standard method **may take up to 72 hours to complete**. If the task is not completed within this time, it is marked as failed, and the $0.01 advance is refunded. It is also important to note that if your account balance is negative, you will not receive the results even if the task is completed successfully.

**Note:** due to the peculiarities of our architecture the queue of completed tasks is updated with a small delay, which can be an issue for high-volume users. If your system requires collecting over 1000 tasks a minute, we recommend using [pingbacks/postbacks](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) instead, and applying the Tasks Ready endpoint only to obtain the IDs of failed postback tasks.

GEThttps://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_responses/tasks_ready

Pricing

Your account will not be charged when receiving results

Each separate task will remain on the list until it is collected. You can make **up to 20 API calls per minute.** With each API call, you can get 1000 tasks completed within three previous days. The list will not contain the tasks which have already been collected and the tasks that were not collected **within the three days** after completion.

Please note that if you specify the `postback_url`, the task will not be in the list of completed tasks. The task can only be found in the list if the request to your server failed, and your server returned HTTP code response less than `200` or higher than `300`.

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total *tasks* cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier***unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*generated by DataForSEO; can be within the following range: 10000-60000you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the parameters passed in the request's URL* |
| **`result`** | array | *array of results* |
| `id` | string | *task identifier of the completed task***unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `se` | string | *LLM model specified when setting the task* |
| `function` | string | *type of the task* |
| `date_posted` | string | *date when the task was posted (in the UTC format)* |
| `tag` | string | *user-defined task identifier* |
| `endpoint` | string | *URL for collecting the results of the task* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Task GET
*Source: [https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_responses/task_get/](https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_responses/task_get/)*
#### Get Chat GPT LLM Responses

Chat GPT LLM Responses endpoint allows you to retrieve structured responses from a specific Chat GPT model, based on the input parameters.

Tasks using the Standard method **may take up to 72 hours to complete**. If the task is not completed within this time, it is marked as failed, and the $0.01 advance is refunded. It is also important to note that if your account balance is negative, you will not receive the results even if the task is completed successfully.

GEThttps://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_responses/task_get/$id

Pricing

Your account will be charged only for posting a task. You can get the results of the task within the next 30 days for free.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/ai-optimization/llm-responses) page.

**Description of the fields for sending a request:**

| Field name | Type | Description |
| --- | --- | --- |
| `id` | string | *task identifier***unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format**you will be able to use it within **30 days** to request the results of the task at any time |

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
| `status_code` | integer | *status code of the task*generated by DataForSEO; can be within the following range: 10000-60000you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD*includes the base task price plus the `money_spent` value |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `model_name` | string | *name of the AI model used* |
| `input_tokens` | integer | *number of tokens in the input*total count of tokens processed |
| `output_tokens` | integer | *number of tokens in the output*total count of tokens generated in the AI response |
| `reasoning_tokens` | integer | *number of reasoning tokens*total count of tokens used to generate reasoning content |
| `web_search` | boolean | *indicates if web search was used* |
| `money_spent` | float | *cost of AI tokens, USD*the price charged by the third-party AI model provider for according to its [Pricing](https://platform.openai.com/docs/pricing) |
| `datetime` | string | *date and time when the result was received*in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”example:`2019-11-15 12:57:46 +00:00` |
| **`items`** | array | *array of response items*contains structured AI response data |
| **`reasoning`** | object | *element in the response* |
| `type` | string | *type of the element = **'reasoning'*****Note:** this element is supported only in reasoning models and is not guaranteed to be returned |
| **`sections`** | array | *reasoning chain sections*array of objects containing the reasoning chain sections generated by the LLM |
| `type` | string | *type of element*=***'summary_text'*** |
| `text` | string | *text of the reasoning chain section*text of the reasoning chain section summarizing the model's thought process |
| **`message`** | object | *element in the response* |
| `type` | string | *type of the element = **'message'*** |
| **`sections`** | array | *array of content sections*contains different parts of the AI response |
| `type` | string | *type of element*=***'text'*** |
| `text` | string | *AI-generated text content* |
| **`annotations`** | array | *array of references used to generate the response*equals `null` if the `web_search` parameter is not set to `true`**Note:** `annotations` may return empty even when `web_search` is `true`, as the AI will attempt to retrieve web information but may not find relevant results |
| `title` | string | *the domain name or title of the quoted source* |
| `url` | string | *URL of the quoted source* |
| `fan_out_queries` | array | *array of fan-out queries*contains related search queries derived from the main query to provide a more comprehensive response |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Live
*Source: [https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_responses/live/](https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_responses/live/)*
#### Live ChatGPT LLM Responses

Live ChatGPT LLM Responses endpoint allows you to retrieve structured responses from a specific ChatGPT AI model, based on the input parameters.

POSThttps://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_responses/live

Pricing

The cost of the task can be calculated on the [Pricing page](https://dataforseo.com/pricing/ai-optimization/llm-responses).

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute, each Live ChatGPT LLM Responses call can contain only one task.

**The number of concurrent Live tasks is currently limited to 30 per account for each platform in the LLM Responses.**

**Execution time for tasks set with the Live ChatGPT LLM Responses endpoint is currently up to 120 seconds.**

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `user_prompt` | string | *prompt for the AI model***required field**the question or task you want to send to the AI model;you can specify **up to 500 characters** in the `user_prompt` field |
| `model_name` | string | *name of the AI model***required field**`model_name`consists of the actual model name and version name;if the basic model name is specified, its latest version will be set by default;for example, if `gpt-4.1` is specified, the `gpt-4.1-2025-04-14` will be set as `model_name` automatically;you can receive the list of available LLM models by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_responses/models](https://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_responses/models)` |
| `max_output_tokens` | integer | *maximum number of tokens in the AI response*optional fieldminimum value for reasoning models (e.g., `reasoning` is `true` in the [Models endpoint](https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_responses/models/)): `1024`;minimum value for non-reasoning models: `16`;maximum value: `4096`;default value: `2048`**Note:** if `web_search` is set to `true` or the reasoning model is specified in the request, the output token count may exceed the specified `max_output_tokens` limit |
| `temperature` | float | *randomness of the AI response*optional fieldhigher values make output more diverse; lower values make output more focused;minimum value: `0`maximum value: `2`default value: `0.94`**Note:** not supported in reasoning models |
| `top_p` | float | *diversity of the AI response*optional field controls diversity of the response by limiting token selection;minimum value: `0`maximum value: `1` default value: `0.92`**Note:** `top_p` cannot be used together with `temperature` in the same request |
| `web_search` | boolean | *enable web search*optional fieldwhen enabled, the AI model can access and cite current web information;default value: `false`;**Note:** refer to the [Models endpoint](https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_responses/models/) for a list of models that support `web_search`; |
| `force_web_search` | boolean | *force AI agent to use web search*optional fieldto enable this parameter, `web_search` must also be enabled;when enabled, the AI model is forced to access and cite current web information;default value: `false`;**Note:** even if the parameter is set to `true`, there is no guarantee web sources will be cited in the response **Note #2:** not supported in reasoning models |
| `web_search_country_iso_code` | string | *ISO country code of the location*optional fieldto enable this parameter, `web_search` must also be enabled;when enabled, the AI model will search the web from the country you specify;**Note:** not supported in `o3-mini`, `o1-pro`, `o1` models |
| `web_search_city` | string | *city name of the location*optional field**Note:** not supported in `o3-mini`, `o1-pro`, `o1` models |
| `system_message` | string | *instructions for the AI behaviour*optional fielddefines the AI's role, tone, or specific behavior you can specify **up to 500 characters** in the `system_message` field |
| `message_chain` | array | *conversation history*optional fieldarray of message objects representing previous conversation turns;each object must contain `role` and `message` parameters:`role` string with either `user` or `ai` role;`message` string with message content (max 500 characters);you can specify ** the maximum of 10 message objects** in the array;example:`"message_chain": [{"role":"user","message":"Hello, what’s up?"},{"role":"ai","message":"Hello! I’m doing well, thank you. How can I assist you today?"}]` |
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
| `status_code` | integer | *status code of the task*generated by DataForSEO; can be within the following range: 10000-60000you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD*includes the base task price plus the `money_spent` value |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `model_name` | string | *name of the AI model used* |
| `input_tokens` | integer | *number of tokens in the input*total count of tokens processed |
| `output_tokens` | integer | *number of tokens in the output*total count of tokens generated in the AI response |
| `reasoning_tokens` | integer | *number of reasoning tokens*total count of tokens used to generate reasoning content |
| `web_search` | boolean | *indicates if web search was used* |
| `money_spent` | float | *cost of AI tokens, USD*the price charged by the third-party AI model provider for according to its [Pricing](https://platform.openai.com/docs/pricing) |
| `datetime` | string | *date and time when the result was received*in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”example:`2019-11-15 12:57:46 +00:00` |
| **`items`** | array | *array of response items*contains structured AI response data |
| **`reasoning`** | object | *element in the response* |
| `type` | string | *type of the element = **'reasoning'*****Note:** this element is supported only in reasoning models and is not guaranteed to be returned |
| **`sections`** | array | *reasoning chain sections*array of objects containing the reasoning chain sections generated by the LLM |
| `type` | string | *type of element*=***'summary_text'*** |
| `text` | string | *text of the reasoning chain section*text of the reasoning chain section summarizing the model's thought process |
| **`message`** | object | *element in the response* |
| `type` | string | *type of the element = **'message'*** |
| **`sections`** | array | *array of content sections*contains different parts of the AI response |
| `type` | string | *type of element*=***'text'*** |
| `text` | string | *AI-generated text content* |
| **`annotations`** | array | *array of references used to generate the response*equals `null` if the `web_search` parameter is not set to `true`**Note:** `annotations` may return empty even when `web_search` is `true`, as the AI will attempt to retrieve web information but may not find relevant results |
| `title` | string | *the domain name or title of the quoted source* |
| `url` | string | *URL of the quoted source* |
| `fan_out_queries` | array | *array of fan-out queries*contains related search queries derived from the main query to provide a more comprehensive response |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Overview
*Source: [https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/overview/](https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/overview/)*
### ChatGPT LLM Scraper: Overview

This API provides structured results from ChatGPT searches

ChatGPT LLM Scraper API allows you to retrieve results from ChatGPT Search mode, based on the keyword and other input paramaters. You can use this API to understand how ChatGPT responds to specific search queries, explore which sources and brands it quotes in its responses.

##### ChatGPT LLM Scraper functions

• [ChatGPT LLM Scraper endpoint](https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/live/advanced/) provides results responses from ChatGPT searches, based on specified keyword and other input parameters.

• [ChatGPT LLM Scraper HTML endpoint](https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/live/html/) provides a raw HTML page of ChatGPT search mode results for the specified keyword, search engine, and location.

To find answers on common questions about AI Optimization API and find guidance on most efficient use, [visit our Help Center.](https://dataforseo.com/help-center/category/ai-optimization-api)

##### Methods

The cost of using ChatGPT LLM Scraper API depends on the selected method and priority of task execution. Available methods and priorities are described below.

DataForSEO has two main methods to deliver the results: Standard and Live.

If your system requires delivering instant results, **[the Live method](https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_responses/live/)** is the best solution for you. Unlike the Standard method, this method doesn’t require making separate POST and GET requests to the corresponding endpoints.

If you don’t need to receive data in real-time, you can use **[the Standard method](https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_responses/task_post/)** of data retrieval. This method requires making separate POST and GET requests, but it’s more affordable. Using this method, you can retrieve the results after our system collects them.

Alternatively, you can specify `pingback_url` or `postback_url` when setting a task, and we will notify you on completion of tasks or send them to you respectively.

If you need to set several tasks, you can receive the list of id for all completed tasks using **[‘Tasks Ready’](https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_responses/tasks_ready/)** endpoint, and then collect the results of each separate task using **[‘Task GET’](https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_responses/task_get/)** endpoint.

Learn more about task completion and obtaining a list of completed tasks in [this Help Center article](https://dataforseo.com/help-center/completed-tasks).

You can send up to 2000 API calls per minute. Contact us if you would like to raise the limit.

Execution time for tasks set with the [Live ChatGPT LLM Scraper endpoint](https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/live/advanced/) is currently **up to 120 seconds**.

##### Priorities and Cost

The Live method delivers results in real-time, and accordingly, the cost of requests made using this method will be the highest.

The Standard method has two different priorities that stand for the relative speed of task execution and have different prices:

1. Normal priority;
2. High priority.

The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/ai-optimization/llm-scraper) page. You can check your spending in your [account dashboard](https://app.dataforseo.com/api-access) or by making a separate call to [the User Data endpoint](https://docs.dataforseo.com/v3/appendix/user_data/?php)

You can test ChatGPT LLM Scraper API for free using DataForSEO [Sandbox.](https://docs.dataforseo.com/v3/appendix/sandbox/)

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

---


##### Locations
*Source: [https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/locations/](https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/locations/)*
#### ChatGPT LLM Scraper Locations List

Pricing

Your account will not be charged for using this API

GEThttps://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/locations

GEThttps://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/locations/$country

You will receive the list of locations by this API call. You can filter the list of locations by country when setting a task.

You can also [download the full list of supported locations](https://cdn.dataforseo.com/v3/locations/locations_ai_optimization_chat_gpt_llm_scraper_2026_06_10.csv) in the CSV format (last updated 2026-06-10).

##### **Note:** All locations in Russia and Belarus are no longer supported across all DataForSEO services due to the invasion of Ukraine.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `country` | string | *country ISO code*optional fieldspecify the ISO code if you want to filter the list of locations by countryexample:`us` |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *general informational message*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total tasks cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier***unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*generated by DataForSEO; can be within the following range: 10000-60000you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the parameters passed in the URL of the GET request* |
| **`result`** | array | *array of results* |
| `location_code` | integer | *location code* |
| `location_name` | string | *full name of the location* |
| `location_code_parent` | integer | *the code of the superordinate location*example:`"location_code": 9041134,"location_name": "Vienna International Airport,Lower Austria,Austria","location_code_parent": 20044`where `location_code_parent` corresponds to:`"location_code": 20044,"location_name": "Lower Austria,Austria"` |
| `country_iso_code` | string | *ISO country code of the location* |
| `location_type` | string | *location type* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Languages
*Source: [https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/languages/](https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/languages/)*
#### ChatGPT LLM Scraper Languages List

Pricing

Your account will not be charged for using this API

GEThttps://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/languages

You will receive the list of languages by calling this API.

You can also [download the full list of supported languages in the CSV format](https://cdn.dataforseo.com/v3/languages/languages_ai_optimization_chat_gpt_llm_scraper_2023_05_02.csv) (last updated 2023-05-02).
 
As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *general informational message*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total tasks cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier***unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*generated by DataForSEO; can be within the following range: 10000-60000you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the parameters passed in the URL of the GET request* |
| **`result`** | array | *array of results* |
| `language_name` | string | *language name* |
| `language_code` | string | *language code according to [ISO 639-1](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes)* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Task POST
*Source: [https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/task_post/](https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/task_post/)*
#### Setting ChatGPT LLM Scraper

ChatGPT LLM Scraper API provides results from ChatGPT searches. The results are specific to the selected location (see [the List of Locations](https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/locations/)) and language (see [the List of Languages](https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/languages/?php)) parameters.

There are two different priorities that stand for the relative speed of task execution: normal and high.

POSThttps://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/task_post

Pricing

Your account will be charged only for setting a task.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/ai-optimization/llm-scraper) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute, with each POST call containing no more than 100 tasks. If your POST call contains over 100 tasks, the tasks over this limit will return the `40006` error.

You can retrieve the results of completed tasks using the unique task identifier `id`. Alternatively, we can send them to you as soon as they are ready if you specify the `postback_url` or `pingback_url` when setting a task. Note that if your server doesn’t respond within 10 seconds, the connection will be aborted by timeout, and the task will be transferred to the [‘Tasks Ready’](https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/tasks_ready/?php) list. The error code and message depend on your server’s configuration. **See [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) to learn more about using pingbacks and postbacks with DataForSEO APIs.**

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `keyword` | string | *keyword***required field**you can specify **up to 2000 characters** in the `keyword` fieldall %## will be decoded (plus character ‘+’ will be decoded to a space character)if you need to use the “%” character for your `keyword`, please specify it as “%25”;if you need to use the “+” character for your `keyword`, please specify it as “%2B”learn more about rules and limitations of `keyword` and `keywords` fields in DataForSEO APIs in this [Help Center article](https://dataforseo.com/help-center/rules-and-limitations-of-keyword-and-keywords-fields-in-dataforseo-apis) |
| `priority` | integer | *task priority*optional fieldcan take the following values:1 – normal execution priority (set by default)2 – high execution priorityYou will be additionally charged for the tasks with high execution priority.The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/ai-optimization/llm-scraper) page. |
| `location_name` | string | *full name of search engine location***required field if you don't specify** `location_code`**if you use this field, you don't need to specify `location_code`**you can receive the list of available locations of the search engine with their `location_name` by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/locations](https://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/locations)`example:`United States` |
| `location_code` | integer | *search engine location code***required field if you don't specify** `location_name`**if you use this field, you don't need to specify `location_name`**you can receive the list of available locations of the search engines with their `location_code` by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/locations](https://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/locations)`example:`2840` |
| `language_name` | string | *full name of search engine language*required field if you don't specify `language_code`;if you use this field, you don't need to specify `language_code`;you can receive the list of available languages of the search engine with their `language_name` by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/languages](https://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/languages)` |
| `language_code` | string | *search engine language code*required field if you don't specify `language_name`;if you use this field, you don't need to specify `language_name`;you can receive the list of available languages of the search engine with their `language_code`_by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/languages](https://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/languages)`n |
| `force_web_search` | boolean | *force AI agent to use web search*optional fieldwhen enabled, the AI model is forced to access and cite current web information;default value: `false`;**Note:** even if the parameter is set to `true`, there is no guarantee web sources will be cited in the response |
| `expand_citations` | boolean | *return expanded citation bar in HTML results*optional fieldto enable this parameter, `force_web_search` must also be enabled;when enabled, the HTML endpoint will return data from the expanded citation bar;default value: `false` |
| `tag` | string | *user-defined task identifier*optional field*the character limit is 255*you can use this parameter to identify the task and match it with the resultyou will find the specified `tag` value in the `data` object of the response |
| `postback_url` | string | *URL for sending task results*optional fieldonce the task is completed, we will send a POST request with its results compressed in the `gzip` format to the `postback_url` you specifiedyou can use the ‘$id’ string as a `$id` variable and ‘$tag’ as urlencoded `$tag` variable. We will set the necessary values before sending the request.example:`[http://your-server.com/postbackscript?id=$id](http://your-server.com/postbackscript?id=$id)``[http://your-server.com/postbackscript?id=$id&tag=$tag](http://your-server.com/postbackscript?id=$id&tag=$tag)`**Note:** special characters in `postback_url` will be urlencoded;i.a., the `#` character will be encoded into `%23`learn more on our [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) |
| `postback_data` | string | *postback_url datatype***required field if you specify `postback_url`**corresponds to the function you used for setting a taskpossible values:`advanced`, `html` |
| `pingback_url` | string | *notification URL of a completed task*optional fieldwhen a task is completed we will notify you by GET request sent to the URL you have specifiedyou can use the ‘$id’ string as a `$id` variable and ‘$tag’ as urlencoded `$tag` variable. We will set the necessary values before sending the request.example:`[http://your-server.com/pingscript?id=$id](http://your-server.com/pingscript?id=$id)``[http://your-server.com/pingscript?id=$id&tag=$tag](http://your-server.com/pingscript?id=$id&tag=$tag)`**Note:** special characters in `pingback_url` will be urlencoded;i.a., the `#` character will be encoded into `%23`learn more on our [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)<br>**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total tasks cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`**array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *unique task identifier in our system*<br>in the [Universally unique identifier (UUID)](https://en.wikipedia.org/wiki/Universally_unique_identifier) format |
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000 |
| `status_message` | string | *informational message of the task* |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| ** `result`** | array | *array of results*<br>in this case, the value will be `null` |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Tasks Ready
*Source: [https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/tasks_ready/](https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/tasks_ready/)*
#### Get ChatGPT LLM Scraper Completed Tasks

The **‘Tasks Ready’** endpoint is designed to provide you with the list of completed tasks, which haven’t been collected yet. If you use the Standard method without specifying the `postback_url`, you can receive the list of `id` for all completed tasks using this endpoint. Then, you can collect the results using the **‘Task GET’** endpoint.
Learn more about task completion and obtaining a list of completed tasks in [this help center article.](https://dataforseo.com/help-center/completed-tasks)

**Note:** due to the peculiarities of our architecture the queue of completed tasks is updated with a small delay, which can be an issue for high-volume users.

If your system requires collecting over 1000 tasks a minute, we recommend using [pingbacks/postbacks](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) instead, and applying the Tasks Ready endpoint only to obtain the IDs of failed postback tasks.

GEThttps://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/tasks_ready

Pricing

Your account is not charged when receiving results

Each separate task will remain on the list until it is collected. You can make **up to 20 API calls per minute.** With each API call, you can get 1000 tasks completed within three previous days. The list will not contain the tasks which have already been collected and the tasks that were not collected **within three days** after completion.

Please note that if you specify the `postback_url`, the task will not be in the list of completed tasks. The task can only be found in the list if the request to your server failed, and your server returned HTTP code response less than `200` or higher than `300`.

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
| `status_code` | integer | *status code of the task*generated by DataForSEO; can be within the following range: 10000-60000you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the parameters passed in the request's URL* |
| **`result`** | array | *array of results* |
| `id` | string | *task identifier of the completed task***unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `se` | string | *search engine specified when setting the task* |
| `se_type` | string | *type of search engine*example: `llm_scraper` |
| `date_posted` | string | *date when the task was posted (in the UTC format)* |
| `tag` | string | *user-defined task identifier* |
| `endpoint_regular` | string | *URL for collecting the results of the Regular task*if the Regular function is not supported in the specified endpoint, the value will be `null` |
| `endpoint_advanced` | string | *URL for collecting the results of the Advanced task*if the Advanced function is not supported in the specified endpoint, the value will be `null` |
| `endpoint_html` | string | *URL for collecting the results of the HTML task*if the HTML function is not supported in the specified endpoint, the value will be `null` |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


###### Advanced
*Source: [https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/task_get/advanced/](https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/task_get/advanced/)*
#### Get ChatGPT LLM Scraper Advanced

GEThttps://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/task_get/advanced/$id

Pricing

Your account will be charged only for posting a task. You can get the results of the task within the next 30 days for free.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/ai-optimization/llm-scraper) page.

**Description of the fields for sending a request:**

| Field name | Type | Description |
| --- | --- | --- |
| `id` | string | *task identifier*[a universally unique identifier (UUID)](https://en.wikipedia.org/wiki/Universally_unique_identifier)**unique task identifier in our system**you will be able to use it within **30 days** to request the results of the task at any time |

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
| `status_code` | integer | *status code of the task*generated by DataForSEO; can be within the following range: 10000-60000you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `keyword` | string | *keyword received in a POST array***the keyword is returned with decoded %## (plus symbol '+' will be decoded to a space character)** |
| `location_code` | integer | *location code in a POST array* |
| `language_code` | string | *language code in a POST array* |
| `model` | string | *indicates the model version* |
| `check_url` | string | *direct URL to search engine results*you can use it to make sure that we provided exact results |
| `datetime` | string | *date and time when the result was received*in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”example:`2019-11-15 12:57:46 +00:00` |
| `markdown` | string | *content of the element in markdown format*content of the result formatted in the [markdown markup language](https://en.wikipedia.org/wiki/Markdown) |
| **`search_results`** | array | *array of search results*all web search outputs the model retrieved when looking up information, including duplicates and unused entries |
| `type` | string | *type of element*=***'chatgpt_search_result'*** |
| `url` | string | *result URL* |
| `domain` | string | *result domain* |
| `title` | string | *result title* |
| `description` | string | *result description* |
| `breadcrumb` | string | *breadcrumb* |
| **`sources`** | array | *array of sources*the sources the model actually cited or relied on in its final answer |
| `type` | string | *type of element*=***'chat_gpt_source'*** |
| `title` | string | *source title* |
| `snippet` | string | *source description* |
| `domain` | string | *source domain in SERP* |
| `url` | string | *source URL* |
| `thumbnail` | string | *source thumbnail* |
| `source_name` | string | *source name* |
| `publication_date` | string | *date and time when the result was published*in the format: “year-month-date:minutes:UTC_difference_hours:UTC_difference_minutes”example:`2019-11-15 12:57:46 +00:00` |
| `markdown` | string | *content of the element in markdown format*content of the result formatted in the [markdown markup language](https://en.wikipedia.org/wiki/Markdown) |
| `fan_out_queries` | array | *array of fan-out queries*contains related search queries derived from the main query to provide a more comprehensive response |
| **`brand_entities`** | array | *array of brand entities*contains information on brands mentioned in the response |
| `type` | string | *type of the element = **'chat_gpt_brand_entity'*** |
| `title` | string | *name of the brand* |
| `category` | string | *category of the brand* |
| `markdown` | string | *brand name in markdown format*contains brand name formatted in the [markdown markup language](https://en.wikipedia.org/wiki/Markdown) |
| **`urls`** | array | * array of URLs and domains relevant to the brand* |
| `url` | string | *URL* |
| `domain` | string | *domain* |
| `se_results_count` | integer | * total number of results* |
| `item_types` | array | *types of search results*contains types of search results (`items`) found.possible item types:`chat_gpt_text`, `chat_gpt_table`, `chat_gpt_navigation_list`, `chat_gpt_images`, `chat_gpt_local_businesses`, `chat_gpt_products` |
| `items_count` | integer | *the number of results returned in the **`items`** array* |
| **`items`** | array | *elements of ChatGPT results* |
| **`chat_gpt_text`** | object | *element in the response* |
| `type` | string | * type of element*=***'chat_gpt_text'*** |
| `rank_group` | integer | *group rank in SERP*position within a group of elements with identical `type` valuespositions of elements with different `type` values are omitted from `rank_group` |
| `rank_absolute` | integer | *absolute rank in SERP*absolute position among all the elements |
| `markdown` | string | *content of the element in markdown format*content of the result formatted in the [markdown markup language](https://en.wikipedia.org/wiki/Markdown) |
| **`sources`** | array | *array of sources* |
| `type` | string | *type of element*=***'chat_gpt_source'*** |
| `title` | string | *source title* |
| `snippet` | string | *source description* |
| `domain` | string | *source domain* |
| `url` | string | *source URL* |
| `thumbnail` | string | *source thumbnail* |
| `source_name` | string | *source name* |
| `publication_date` | string | *date and time when the result was published*in the format: “year-month-date:minutes:UTC_difference_hours:UTC_difference_minutes”example:`2019-11-15 12:57:46 +00:00` |
| `markdown` | string | *content of the element in markdown format*content of the result formatted in the [markdown markup language](https://en.wikipedia.org/wiki/Markdown) |
| **`brand_entities`** | array | *array of brand entities*contains information on brands mentioned in the text |
| `type` | string | *type of the element = **'chat_gpt_brand_entity'*** |
| `title` | string | *name of the brand* |
| `category` | string | *category of the brand* |
| `markdown` | string | *brand name in markdown format*contains brand name formatted in the [markdown markup language](https://en.wikipedia.org/wiki/Markdown) |
| **`urls`** | array | * array of URLs and domains relevant to the brand * |
| `url` | string | *URL* |
| `domain` | string | *domain* |
| **`chat_gpt_table`** | object | *element in the response* |
| `type` | string | * type of element*=***'chat_gpt_table'*** |
| `rank_group` | integer | *group rank in SERP*position within a group of elements with identical `type` valuespositions of elements with different `type` values are omitted from `rank_group` |
| `rank_absolute` | integer | *absolute rank in SERP*absolute position among all the elements in SERP |
| `text` | string | *text of the element* |
| `markdown` | string | *content of the element in markdown format*content of the result formatted in the [markdown markup language](https://en.wikipedia.org/wiki/Markdown) |
| **`table`** | object | *table present in the element*the header and content of the table present in the element |
| `table_header` | array | *content in the header of the table* |
| `table_content` | array | *array of contents of the table present in the element*each array represents the table row |
| **`brand_entities`** | array | *array of brand entities*contains information on brands mentioned in the table |
| `type` | string | *type of the element = **'chat_gpt_brand_entity'*** |
| `title` | string | *name of the brand* |
| `category` | string | *category of the brand* |
| `markdown` | string | *brand name in markdown format*contains brand name formatted in the [markdown markup language](https://en.wikipedia.org/wiki/Markdown) |
| **`urls`** | array | * array of URLs and domains relevant to the brand * |
| `url` | string | *URL* |
| `domain` | string | *domain* |
| **`chat_gpt_navigation_list`** | object | *element in the response* |
| `type` | string | * type of element*=***'chat_gpt_navigation_list'*** |
| `rank_group` | integer | *group rank in SERP*position within a group of elements with identical `type` valuespositions of elements with different `type` values are omitted from `rank_group` |
| `rank_absolute` | integer | *absolute rank in SERP*absolute position among all the elements in SERP |
| `title` | string | *title of the element* |
| **`sources`** | array | *array of sources* |
| `type` | string | *type of element*=***'chat_gpt_source'*** |
| `title` | string | *source title* |
| `snippet` | string | *source description* |
| `domain` | string | *source domain* |
| `url` | string | *source URL* |
| `thumbnail` | string | *source thumbnail* |
| `source_name` | string | *source name* |
| `publication_date` | string | *date and time when the result was published*in the format: “year-month-date:minutes:UTC_difference_hours:UTC_difference_minutes”example:`2019-11-15 12:57:46 +00:00` |
| `markdown` | string | *content of the element in markdown format*content of the result formatted in the [markdown markup language](https://en.wikipedia.org/wiki/Markdown) |
| **`chat_gpt_images`** | object | *element in the response* |
| `type` | string | * type of element*=***'chat_gpt_images'*** |
| `rank_group` | integer | *group rank in SERP*position within a group of elements with identical `type` valuespositions of elements with different `type` values are omitted from `rank_group` |
| `rank_absolute` | integer | *absolute rank in SERP*absolute position among all the elements in SERP |
| `markdown` | string | *content of the element in markdown format*content of the result formatted in the [markdown markup language](https://en.wikipedia.org/wiki/Markdown) |
| **`items`** | array | *items present in the element* |
| `type` | string | *type of element = '**chat_gpt_images_element**'* |
| `alt` | string | *alt tag of the image* |
| `url` | string | *relevant URL* |
| `image_url` | string | *URL of the image*the URL leading to the image on the original resource or DataForSEO storage (in case the original source is not available) |
| `markdown` | string | *content of the element in markdown format*content of the result formatted in the [markdown markup language](https://en.wikipedia.org/wiki/Markdown) |
| **`chat_gpt_local_businesses`** | object | *element in the response* |
| `type` | string | * type of element*=***'chat_gpt_local_businesses'*** |
| `rank_group` | integer | *group rank in SERP*position within a group of elements with identical `type` valuespositions of elements with different `type` values are omitted from `rank_group` |
| `rank_absolute` | integer | *absolute rank in SERP*absolute position among all the elements in SERP |
| `markdown` | string | *content of the element in markdown format*content of the result formatted in the [markdown markup language](https://en.wikipedia.org/wiki/Markdown) |
| **`items`** | array | *items present in the element* |
| `type` | string | *type of element = '**chat_gpt_local_businesses_element**'* |
| `title` | string | *title of the local business* |
| `description` | string | *description of the local business* |
| `address` | string | *address of the local business* |
| `phone` | string | *phone of the local business* |
| `reviews_count` | integer | *total number of reviews submitted for the local business* |
| `url` | string | *website URL of the local business* |
| `domain` | string | *domain name of the local business* |
| **`rating`** | object | *rating of the corresponding local business*popularity rate based on reviews as displayed in the results |
| `rating_type` | string | *type of rating*here you can find the following elements: `Max5`, `Percents`, `CustomMax` |
| `value` | float | *the average rating based on all reviews* |
| `votes_count` | integer | *the number of votes* |
| `rating_max` | integer | *the maximum value for a `rating_type`* |
| **`chat_gpt_products`** | object | *element in the response* |
| `type` | string | * type of element*=***'chat_gpt_products'*** |
| `rank_group` | integer | *group rank in SERP*position within a group of elements with identical `type` valuespositions of elements with different `type` values are omitted from `rank_group` |
| `rank_absolute` | integer | *absolute rank in SERP*absolute position among all the elements in SERP |
| **`items`** | array | *items present in the element* |
| `type` | string | *type of element = '**chat_gpt_products_element**'* |
| `product_id` | string | *product id* |
| `merchants` | string | *merchant(s) offering the product* |
| `id_to_token_map` | string | *product identifier token*Base64-encoded token containing Google Shopping product IDs associated with the product |
| `title` | string | *title of the product* |
| **`rating`** | object | *rating of the product*popularity rate based on reviews and displayed in SERP |
| `rating_type` | string | *type of rating*here you can find the following elements: `Max5`, `Percents`, `CustomMax` |
| `value` | float | *the average rating based on all reviews* |
| `votes_count` | integer | *the number of votes* |
| `rating_max` | integer | *the maximum value for a `rating_type`* |
| `price` | float | *product price* |
| `currency` | string | *currency of the listed price*ISO code of the currency applied to the price |
| `tag` | string | *tag text* |
| `url` | string | *result URL* |
| `domain` | string | *result domain* |
| `images` | array | *image URLs of the element*contains URLs leading to the images on the original resource or DataForSEO storage (in case the original source is not available) |
| **`product_ids`** | array | *Google Shopping product identifiers*array of Google Shopping product IDs associated with the product |
| `type` | string | *type of element = '**chat_gpt_google_shopping_product**'* |
| `ei` | string | *event identifier*internal event identifier used by Google |
| `product_id` | string | *product identifier*can be used as a `data_docid` in [Google Shopping API endpoints](https://docs.dataforseo.com/v3/merchant/google/overview/) |
| `catalog_id` | string | *Google Shopping catalog identifier of the product*can be used as a `product_id` in [Google Shopping API endpoints](https://docs.dataforseo.com/v3/merchant/google/overview/) |
| `gpcid` | string | *Google product cluster identifier*can be used as a `gid` in [Google Shopping API endpoints](https://docs.dataforseo.com/v3/merchant/google/overview/) |
| `headline_offer_docid` | string | *document identifier of the main offer in the headline*can be used as a `data_docid` in [Google Shopping API endpoints](https://docs.dataforseo.com/v3/merchant/google/overview/) |
| `image_docid` | string | *identifier for the displayed product’s image* |
| `rds` | string | *resource descriptor string *internal Google resource descriptor string that identifies the product within Google's Shopping index |
| `query` | string | *search query*search query used by ChatGPT to retrieve the product from Google Shopping |
| `mid` | string | *merchant identifier*identifier of the seller or merchant account in Google Shopping |
| `pvt` | string | *product view type*internal Google parameter that specifies the product view type used when rendering the product item |
| `uule` | string | *encoded location parameter*indicates the location for a search |
| `gl` | string | *country code*indicates the location for which search results are displayed |
| `hl` | string | *host language code*indicates the language in which search results are displayed |
| **`chat_gpt_ad`** | object | *element in the response* |
| `type` | string | * type of element*=***'chat_gpt_ad'*** |
| `rank_group` | integer | *group rank in SERP*position within a group of elements with identical `type` valuespositions of elements with different `type` values are omitted from `rank_group` |
| `rank_absolute` | integer | *absolute rank in SERP*absolute position among all the elements in SERP |
| `title` | string | *title of the ad* |
| `snippet` | string | *description text of the ad* |
| `url` | string | *URL of the ad landing page* |
| `domain` | string | *domain of the ad landing page* |
| `image_url` | string | *URL of the image displayed in the ad* |
| **`advertiser`** | object | *information about the advertiser associated with the ad* |
| `name` | string | *name of the advertiser* |
| `url` | string | *URL of the advertiser's website* |
| `favicon_url` | string | *URL of the advertiser's favicon image* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


###### HTML
*Source: [https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/task_get/html/](https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/task_get/html/)*
#### Get ChatGPT LLM Scraper HTML

GEThttps://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/task_get/html/$id

Pricing

Your account will be charged only for posting a task. You can get the results of the task within the next 7 days for free.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/ai-optimization/llm-scraper) page.

**Description of the fields for sending a request:**

| Field name | Type | Description |
| --- | --- | --- |
| `id` | string | *task identifier***unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format**you will be able to use it within **7 days** to request the results of the task at any time |

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
| `status_code` | integer | *status code of the task*generated by DataForSEO; can be within the following range: 10000-60000you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `keyword` | string | *keyword received in a POST array***keyword is returned with decoded %## (plus symbol '+' will be decoded to a space character)** |
| `location_code` | integer | *location code in a POST array* |
| `language_code` | string | *language code in a POST array* |
| `datetime` | string | *date and time when the result was received*in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”example:`2019-11-15 12:57:46 +00:00` |
| `items_count` | integer | *the number of results returned in the **`items`** array* |
| **`items`** | array | *elements of search results found* |
| `page` | integer | *serial number of the returned HTML page* |
| `date` | string | *date and time when the HTML page was scanned*in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”example:`2019-11-15 12:57:46 +00:00` |
| `html` | string | *HTML page* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


###### Advanced
*Source: [https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/live/advanced/](https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/live/advanced/)*
#### Live ChatGPT LLM Scraper Advanced

Live ChatGPT LLM Scraper endpoint provides results from ChatGPT searches. The results are specific to the selected location (see [the List of Locations](https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/locations/)) and language (see [the List of Languages](https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/languages/)) parameters.

POSThttps://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/live/advanced

Pricing

The cost of the task can be calculated on the [Pricing page](https://dataforseo.com/pricing/ai-optimization/llm-scraper).

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute, each Live ChatGPT LLM Scraper API call can contain only one task.

**Execution time for tasks set with the Live ChatGPT LLM Scraper endpoint is currently up to 120 seconds.**

Below you will find a detailed description of the fields you can use for setting a task.

| Field name | Type | Description |
| --- | --- | --- |
| `keyword` | string | *keyword***required field**you can specify **up to 2000 characters** in the `keyword` fieldall %## will be decoded (plus character ‘+’ will be decoded to a space character)if you need to use the “%” character for your `keyword`, please specify it as “%25”;if you need to use the “+” character for your `keyword`, please specify it as “%2B”learn more about rules and limitations of `keyword` and `keywords` fields in DataForSEO APIs in this [Help Center article](https://dataforseo.com/help-center/rules-and-limitations-of-keyword-and-keywords-fields-in-dataforseo-apis) |
| `location_name` | string | *full name of search engine location***required field if you don't specify** `location_code`**if you use this field, you don't need to specify `location_code`**you can receive the list of available locations of the search engine with their `location_name` by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/locations](https://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/locations)`example:`United States` |
| `location_code` | integer | *search engine location code***required field if you don't specify** `location_name`**if you use this field, you don't need to specify `location_name`**you can receive the list of available locations of the search engines with their `location_code` by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/locations](https://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/locations)`example:`2840` |
| `language_name` | string | *full name of search engine language***required field if you don't specify `language_code`;**if you use this field, you don't need to specify `language_code`;you can receive the list of available languages of the search engine with their `language_name` by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/languages](https://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/languages)` |
| `language_code` | string | *search engine language code***required field if you don't specify `language_name`;**if you use this field, you don't need to specify `language_name`;you can receive the list of available languages of the search engine with their `language_code` by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/languages](https://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/languages)` |
| `force_web_search` | boolean | *force AI agent to use web search*optional fieldwhen enabled, the AI model is forced to access and cite current web information;default value: `false`;**Note:** even if the parameter is set to `true`, there is no guarantee web sources will be cited in the response |
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
| `status_code` | integer | *status code of the task*generated by DataForSEO; can be within the following range: 10000-60000you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `keyword` | string | *keyword received in a POST array***the keyword is returned with decoded %## (plus symbol '+' will be decoded to a space character)** |
| `location_code` | integer | *location code in a POST array* |
| `language_code` | string | *language code in a POST array* |
| `model` | string | *indicates the model version* |
| `check_url` | string | *direct URL to search engine results*you can use it to make sure that we provided exact results |
| `datetime` | string | *date and time when the result was received*in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”example:`2019-11-15 12:57:46 +00:00` |
| `markdown` | string | *content of the element in markdown format*content of the result formatted in the [markdown markup language](https://en.wikipedia.org/wiki/Markdown) |
| **`search_results`** | array | *array of search results*all web search outputs the model retrieved when looking up information, including duplicates and unused entries |
| `type` | string | *type of element*=***'chatgpt_search_result'***n |
| `url` | string | *result URL* |
| `domain` | string | *result domain* |
| `title` | string | *result title* |
| `description` | string | *result description* |
| `breadcrumb` | string | *breadcrumb* |
| **`sources`** | array | *array of sources*the sources the model actually cited or relied on in its final answer |
| `type` | string | *type of element*=***'chat_gpt_source'*** |
| `title` | string | *source title* |
| `snippet` | string | *source description* |
| `domain` | string | *source domain* |
| `url` | string | *source URL* |
| `thumbnail` | string | *source thumbnail* |
| `source_name` | string | *source name* |
| `publication_date` | string | *date and time when the result was published*in the format: “year-month-date:minutes:UTC_difference_hours:UTC_difference_minutes”example:`2019-11-15 12:57:46 +00:00` |
| `markdown` | string | *content of the element in markdown format*content of the result formatted in the [markdown markup language](https://en.wikipedia.org/wiki/Markdown) |
| `fan_out_queries` | array | *array of fan-out queries*contains related search queries derived from the main query to provide a more comprehensive response |
| **`brand_entities`** | array | *array of brand entities*contains information on brands mentioned in the response |
| `type` | string | *type of the element = **'chat_gpt_brand_entity'*** |
| `title` | string | *name of the brand* |
| `category` | string | *category of the brand* |
| `markdown` | string | *brand name in markdown format*contains brand name formatted in the [markdown markup language](https://en.wikipedia.org/wiki/Markdown) |
| **`urls`** | array | * array of URLs and domains relevant to the brand* |
| `url` | string | *URL* |
| `domain` | string | *domain* |
| `se_results_count` | integer | * total number of results* |
| `item_types` | array | *types of search results*contains types of search results (`items`) found in SERP.possible item types:`chat_gpt_text`, `chat_gpt_table`, `chat_gpt_navigation_list`, `chat_gpt_images`, `chat_gpt_local_businesses`, `chat_gpt_products` |
| `items_count` | integer | *the number of results returned in the **`items`** array* |
| **`items`** | array | *elements of ChatGPT results* |
| **`chat_gpt_text`** | object | *element in the response* |
| `type` | string | * type of element*=***'chat_gpt_text'*** |
| `rank_group` | integer | *group rank in SERP*position within a group of elements with identical `type` valuespositions of elements with different `type` values are omitted from `rank_group` |
| `rank_absolute` | integer | *absolute rank in SERP*absolute position among all the elements in SERP |
| `markdown` | string | *content of the element in markdown format*content of the result formatted in the [markdown markup language](https://en.wikipedia.org/wiki/Markdown) |
| **`sources`** | array | *array of sources* |
| `type` | string | *type of element*=***'chat_gpt_source'***n |
| `title` | string | *source title* |
| `snippet` | string | *source description* |
| `domain` | string | *source domain in SERP* |
| `url` | string | *source URL* |
| `thumbnail` | string | *source thumbnail* |
| `source_name` | string | *source name* |
| `publication_date` | string | *date and time when the result was published*in the format: “year-month-date:minutes:UTC_difference_hours:UTC_difference_minutes”example:`2019-11-15 12:57:46 +00:00` |
| `markdown` | string | *content of the element in markdown format*content of the result formatted in the [markdown markup language](https://en.wikipedia.org/wiki/Markdown) |
| **`brand_entities`** | array | *array of brand entities*contains information on brands mentioned in the text |
| `type` | string | *type of the element = **'chat_gpt_brand_entity'*** |
| `title` | string | *name of the brand* |
| `category` | string | *category of the brand* |
| `markdown` | string | *brand name in markdown format*contains brand name formatted in the [markdown markup language](https://en.wikipedia.org/wiki/Markdown) |
| **`urls`** | array | * array of URLs and domains relevant to the brand * |
| `url` | string | *URL* |
| `domain` | string | *domain* |
| **`chat_gpt_table`** | object | *element in the response* |
| `type` | string | * type of element*=***'chat_gpt_table'*** |
| `rank_group` | integer | *group rank in SERP*position within a group of elements with identical `type` valuespositions of elements with different `type` values are omitted from `rank_group` |
| `rank_absolute` | integer | *absolute rank in SERP*absolute position among all the elements in SERP |
| `text` | string | *text of the element* |
| `markdown` | string | *content of the element in markdown format*content of the result formatted in the [markdown markup language](https://en.wikipedia.org/wiki/Markdown) |
| **`table`** | object | *table present in the element*the header and content of the table present in the element |
| `table_header` | array | *content in the header of the table* |
| `table_content` | array | *array of contents of the table present in the element*each array represents the table row |
| **`brand_entities`** | array | *array of brand entities*contains information on brands mentioned in the table |
| `type` | string | *type of the element = **'chat_gpt_brand_entity'*** |
| `title` | string | *name of the brand* |
| `category` | string | *category of the brand* |
| `markdown` | string | *brand name in markdown format*contains brand name formatted in the [markdown markup language](https://en.wikipedia.org/wiki/Markdown) |
| **`urls`** | array | * array of URLs and domains relevant to the brand * |
| `url` | string | *URL* |
| `domain` | string | *domain* |
| **`chat_gpt_navigation_list`** | object | *element in the response* |
| `type` | string | * type of element*=***'chat_gpt_navigation_list'*** |
| `rank_group` | integer | *group rank in SERP*position within a group of elements with identical `type` valuespositions of elements with different `type` values are omitted from `rank_group` |
| `rank_absolute` | integer | *absolute rank in SERP*absolute position among all the elements in SERP |
| `title` | string | *title of the element* |
| **`sources`** | array | *array of sources* |
| `type` | string | *type of element*=***'chat_gpt_source'*** |
| `title` | string | *source title* |
| `snippet` | string | *source description* |
| `domain` | string | *source domain in SERP* |
| `url` | string | *source URL* |
| `thumbnail` | string | *source thumbnail* |
| `source_name` | string | *source name* |
| `publication_date` | string | *date and time when the result was published*in the format: “year-month-date:minutes:UTC_difference_hours:UTC_difference_minutes”example:`2019-11-15 12:57:46 +00:00` |
| `markdown` | string | *content of the element in markdown format*content of the result formatted in the [markdown markup language](https://en.wikipedia.org/wiki/Markdown) |
| **`chat_gpt_images`** | object | *element in the response* |
| `type` | string | * type of element*=***'chat_gpt_images'*** |
| `rank_group` | integer | *group rank in SERP*position within a group of elements with identical `type` valuespositions of elements with different `type` values are omitted from `rank_group` |
| `rank_absolute` | integer | *absolute rank in SERP*absolute position among all the elements in SERP |
| `markdown` | string | *content of the element in markdown format*content of the result formatted in the [markdown markup language](https://en.wikipedia.org/wiki/Markdown) |
| **`items`** | array | *items present in the element* |
| `type` | string | *type of element = '**chat_gpt_images_element**'* |
| `alt` | string | *alt tag of the image* |
| `url` | string | *relevant URL* |
| `image_url` | string | *URL of the image*the URL leading to the image on the original resource or DataForSEO storage (in case the original source is not available) |
| `markdown` | string | *content of the element in markdown format*content of the result formatted in the [markdown markup language](https://en.wikipedia.org/wiki/Markdown) |
| **`chat_gpt_local_businesses`** | object | *element in the response* |
| `type` | string | * type of element*=***'chat_gpt_local_businesses'*** |
| `rank_group` | integer | *group rank in SERP*position within a group of elements with identical `type` valuespositions of elements with different `type` values are omitted from `rank_group` |
| `rank_absolute` | integer | *absolute rank in SERP*absolute position among all the elements in SERP |
| `markdown` | string | *content of the element in markdown format*content of the result formatted in the [markdown markup language](https://en.wikipedia.org/wiki/Markdown) |
| **`items`** | array | *items present in the element* |
| `type` | string | *type of element = '**chat_gpt_local_businesses_element**'* |
| `title` | string | *title of the local business* |
| `description` | string | *description of the local business* |
| `address` | string | *address of the local business* |
| `phone` | string | *phone of the local business* |
| `reviews_count` | integer | *total number of reviews submitted for the local business* |
| `url` | string | *website URL of the local business* |
| `domain` | string | *domain name of the local business* |
| **`rating`** | object | *rating of the corresponding local business*popularity rate based on reviews and displayed in SERP |
| `rating_type` | string | *type of rating*here you can find the following elements: `Max5`, `Percents`, `CustomMax` |
| `value` | float | *the average rating based on all reviews* |
| `votes_count` | integer | *the number of votes* |
| `rating_max` | integer | *the maximum value for a `rating_type`* |
| **`chat_gpt_products`** | object | *element in the response* |
| `type` | string | * type of element*=***'chat_gpt_products'*** |
| `rank_group` | integer | *group rank in SERP*position within a group of elements with identical `type` valuespositions of elements with different `type` values are omitted from `rank_group` |
| `rank_absolute` | integer | *absolute rank in SERP*absolute position among all the elements in SERP |
| **`items`** | array | *items present in the element* |
| `type` | string | *type of element = '**chat_gpt_products_element**'* |
| `product_id` | string | *product id* |
| `merchants` | string | *merchant(s) offering the product* |
| `id_to_token_map` | string | *product identifier token*Base64-encoded token containing Google Shopping product IDs associated with the product |
| `title` | string | *title of the product* |
| **`rating`** | object | *rating of the product*popularity rate based on reviews and displayed in SERP |
| `rating_type` | string | *type of rating*here you can find the following elements: `Max5`, `Percents`, `CustomMax` |
| `value` | float | *the average rating based on all reviews* |
| `votes_count` | integer | *the number of votes* |
| `rating_max` | integer | *the maximum value for a `rating_type`* |
| `price` | float | *product price* |
| `currency` | string | *currency of the listed price*ISO code of the currency applied to the price |
| `tag` | string | *tag text* |
| `url` | string | *result URL* |
| `domain` | string | *result domain in SERP* |
| `images` | array | *image URLs of the element*contains URLs leading to the images on the original resource or DataForSEO storage (in case the original source is not available) |
| **`product_ids`** | array | *Google Shopping product identifiers*array of Google Shopping product IDs associated with the product |
| `type` | string | *type of element = '**chat_gpt_google_shopping_product**'* |
| `ei` | string | *event identifier*internal event identifier used by Google |
| `product_id` | string | *product identifier*can be used as a `data_docid` in [Google Shopping API endpoints](https://docs.dataforseo.com/v3/merchant/google/overview/) |
| `catalog_id` | string | *Google Shopping catalog identifier of the product*can be used as a `product_id` in [Google Shopping API endpoints](https://docs.dataforseo.com/v3/merchant/google/overview/) |
| `gpcid` | string | *Google product cluster identifier*can be used as a `gid` in [Google Shopping API endpoints](https://docs.dataforseo.com/v3/merchant/google/overview/) |
| `headline_offer_docid` | string | *document identifier of the main offer in the headline*can be used as a `data_docid` in [Google Shopping API endpoints](https://docs.dataforseo.com/v3/merchant/google/overview/) |
| `image_docid` | string | *identifier for the displayed product’s image* |
| `rds` | string | *resource descriptor string *internal Google resource descriptor string that identifies the product within Google's Shopping index |
| `query` | string | *search query*search query used by ChatGPT to retrieve the product from Google Shopping |
| `mid` | string | *merchant identifier*identifier of the seller or merchant account in Google Shopping |
| `pvt` | string | *product view type*internal Google parameter that specifies the product view type used when rendering the product item |
| `uule` | string | *encoded location parameter*indicates the location for a search |
| `gl` | string | *country code*indicates the location for which search results are displayed |
| `hl` | string | *host language code*indicates the language in which search results are displayed |
| **`chat_gpt_ad`** | object | *element in the response* |
| `type` | string | * type of element*=***'chat_gpt_ad'*** |
| `rank_group` | integer | *group rank in SERP*position within a group of elements with identical `type` valuespositions of elements with different `type` values are omitted from `rank_group` |
| `rank_absolute` | integer | *absolute rank in SERP*absolute position among all the elements in SERP |
| `title` | string | *title of the ad* |
| `snippet` | string | *description text of the ad* |
| `url` | string | *URL of the ad landing page* |
| `domain` | string | *domain of the ad landing page* |
| `image_url` | string | *URL of the image displayed in the ad* |
| **`advertiser`** | object | *information about the advertiser associated with the ad* |
| `name` | string | *name of the advertiser* |
| `url` | string | *URL of the advertiser's website* |
| `favicon_url` | string | *URL of the advertiser's favicon image* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


###### HTML
*Source: [https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/live/html/](https://docs.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/live/html/)*
#### Live ChatGPT LLM Scraper HTML

Live ChatGPT LLM Scraper API HTML provides a raw HTML page of the results for the specified keyword, language, and location.

POSThttps://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/live/html

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/ai-optimization/llm-scraper) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute, each Live LLM Scraper API call can contain only one task.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `keyword` | string | *keyword***required field**you can specify **up to 2000 characters** in the `keyword` fieldall %## will be decoded (plus character ‘+’ will be decoded to a space character)if you need to use the “%” character for your `keyword`, please specify it as “%25”;if you need to use the “+” character for your `keyword`, please specify it as “%2B”learn more about rules and limitations of `keyword` and `keywords` fields in DataForSEO APIs in this [Help Center article](https://dataforseo.com/help-center/rules-and-limitations-of-keyword-and-keywords-fields-in-dataforseo-apis) |
| `location_name` | string | *full name of search engine location***required field if you don't specify** `location_code`**if you use this field, you don't need to specify `location_code`**you can receive the list of available locations of the search engine with their `location_name` by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/chat_gpt/locations](https://api.dataforseo.com/v3/ai_optimization/chat_gpt/locations)`example:`United States` |
| `location_code` | integer | *search engine location code***required field if you don't specify** `location_name`**if you use this field, you don't need to specify `location_name`**you can receive the list of available locations of the search engines with their `location_code` by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/locations](https://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/locations)`example:`2840` |
| `language_name` | string | *full name of search engine language***required field if you don't specify** `language_code`**if you use this field, you don't need to specify `language_code`**you can receive the list of available languages of the search engine with their `language_name` by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/languages](https://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/languages)`example:`English` |
| `language_code` | string | *search engine language code***required field if you don't specify** `language_name`**if you use this field, you don't need to specify `language_name`**you can receive the list of available languages of the search engine with their `language_code`_by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/languages](https://api.dataforseo.com/v3/ai_optimization/chat_gpt/llm_scraper/languages)`example:`en`n |
| `force_web_search` | boolean | *force AI agent to use web search*optional fieldwhen enabled, the AI model is forced to access and cite current web information;default value: `false`;**Note:** even if the parameter is set to `true`, there is no guarantee web sources will be cited in the response |
| `expand_citations` | boolean | *return expanded citation bar in HTML results*optional fieldto enable this parameter, `force_web_search` must also be enabled;when enabled, the endpoint will return HTML data from the expanded citation bar;default value: `false` |
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
| `status_code` | integer | *status code of the task*generated by DataForSEO; can be within the following range: 10000-60000you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the **`result`** array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `keyword` | string | *keyword received in a POST array***keyword is returned with decoded %## (plus character '+' will be decoded to a space character)** |
| `location_code` | integer | *location code in a POST array* |
| `language_code` | string | *language code in a POST array* |
| `datetime` | string | *date and time when the result was received*in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”example:`2019-11-15 12:57:46 +00:00` |
| `items_count` | integer | *the number of results returned in the **`items`** array* |
| **`items`** | array | *elements of search results found* |
| `page` | integer | *serial number of the returned HTML page* |
| `date` | string | *date and time when the HTML page was scanned*in the format: “year-month-date:minutes:UTC_difference_hours:UTC_difference_minutes”example:`2019-11-15 12:57:46 +00:00` |
| `html` | string | *HTML page* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Overview
*Source: [https://docs.dataforseo.com/v3/ai_optimization/claude/llm_responses/overview/](https://docs.dataforseo.com/v3/ai_optimization/claude/llm_responses/overview/)*
### Claude LLM Responses: Overview

This API allows you to generate and retrieve structured Claude responses

LLM Responses Claude API enables generation of structured responses from Claude, based on your specified input parameters. You can use this API to discover how Claude responds to queries about your brand, product, competitors, or any other target keywords and topics.

The endpoints of this API include:

• [Claude LLM Responses endpoint](https://docs.dataforseo.com/v3/ai_optimization/claude/llm_responses/live/) retrieves structured responses from a specific Claude AI model, based on your input parameters.

• [Claude Models LLM Responses endpoint](https://docs.dataforseo.com/v3/ai_optimization/claude/llm_responses/models/) provides a list of available Claude AI models you can use with LLM Responses Claude endpoint.

To find answers on common questions about AI Optimization API and find guidance on most efficient use, [visit our Help Center.](https://dataforseo.com/help-center/category/ai-optimization-api)

##### Methods

The cost of using Claude LLM Responses API depends on the selected method and priority of task execution. Available methods and priorities are described below.

DataForSEO has two main methods to deliver the results: Standard and Live.

If your system requires delivering instant results, **the Live method** is the best solution for you. Unlike the Standard method, this method doesn’t require making separate POST and GET requests to the corresponding endpoints.

If you don’t need to receive data in real-time, you can use **the Standard method** of data retrieval. This method requires making separate POST and GET requests, but it’s more affordable. Using this method, you can retrieve the results after our system collects them.

Alternatively, you can specify `pingback_url` or `postback_url` when setting a task, and we will notify you on completion of tasks or send them to you respectively.

If you need to set several tasks, you can receive the list of id for all completed tasks using **‘Tasks Ready’** endpoint, and then collect the results of each separate task using **‘Task GET’** endpoint.

You can send up to 2000 API calls per minute. Contact us if you would like to raise the limit. Note that the maximum number of Live requests that can be sent simultaneously **is limited to 30** per account for each platform in the LLM Responses.

Execution time for tasks set using [the Live method](https://docs.dataforseo.com/v3/ai_optimization/claude/llm_responses/live/) is currently **up to 120 seconds**. Tasks set using [the Standard method](https://docs.dataforseo.com/v3/ai_optimization/claude/llm_responses/task_post/) **may take up to 72 hours to complete**.

##### Cost

The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/ai-optimization/llm-responses) page. You can check your spending in your [account dashboard](https://app.dataforseo.com/api-access) or by making a separate call to [the User Data endpoint](https://docs.dataforseo.com/v3/appendix/user_data/?php)

You can test Claude LLM Responses API for free using DataForSEO [Sandbox.](https://docs.dataforseo.com/v3/appendix/sandbox/)

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

---


##### Models
*Source: [https://docs.dataforseo.com/v3/ai_optimization/claude/llm_responses/models/](https://docs.dataforseo.com/v3/ai_optimization/claude/llm_responses/models/)*
#### Claude Models LLM Responses List

Pricing

Your account will not be charged for using this API

GEThttps://api.dataforseo.com/v3/ai_optimization/claude/llm_responses/models

You will receive the list of available Claude AI models by calling this API.
 
As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *general informational message*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total tasks cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier***unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*generated by DataForSEO; can be within the following range: 10000-60000you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the parameters passed in the URL of the GET request* |
| **`result`** | array | *array of results* |
| `model_name` | string | *name of the AI model* |
| `reasoning` | boolean | *indicates if the AI model supports reasoning* |
| `web_search_supported` | boolean | *web search support for the AI model*if `true`, the `web_search` parameter can be set with the AI model |
| `task_post_supported` | boolean | *indicates if Standard (POST-GET) data retrieval is supported*if `true`, you can use the [Standard (POST-GET)](https://dataforseo.com/help-center/live-vs-standard-method) data retrieval method with the AI model |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Task POST
*Source: [https://docs.dataforseo.com/v3/ai_optimization/claude/llm_responses/task_post/](https://docs.dataforseo.com/v3/ai_optimization/claude/llm_responses/task_post/)*
#### Setting Claude LLM Responses Tasks

Claude LLM Responses endpoint allows you to retrieve structured responses from a specific Claude model, based on the input parameters.

This is the Standard method of data retrieval. If you don’t need to receive data in real-time, this method is the best option for you. Set a task and retrieve the results when our system collects them. Execution time depends on the system workload.

If your system requires delivering instant results, [the Live method](https://docs.dataforseo.com/v3/ai_optimization-claude-llm_responses-live/) will be a better solution. This method doesn’t require making separate POST and GET requests to the corresponding endpoints.

Note that this endpoint requires making an automatic prepayment of $0.01 to execute the task. If the cost charged by the LLM is less than $0.01, the difference will be refunded to your account balance.

POSThttps://api.dataforseo.com/v3/ai_optimization/claude/llm_responses/task_post

Pricing

Your account will be charged only for setting a task.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/ai-optimization/llm-responses) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). Task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute, with each POST call containing no more than 100 tasks. If your POST call contains over 100 tasks, the tasks over this limit will return the `40006` error.

Tasks using the Standard method **may take up to 72 hours to complete**. If the task is not completed within this time, it is marked as failed, and the $0.01 advance is refunded. It is also important to note that if your account balance is negative, you will not receive the results even if the task is completed successfully.

You can also retrieve the results of completed tasks using the unique task identifier `id`. Alternatively, we can send them to you as soon as they are ready if you specify the `postback_url` or `pingback_url` when setting a task. Note that if your server doesn’t respond within 10 seconds, the connection will be aborted by timeout, and the task will be transferred to the [tasks_ready](https://docs.dataforseo.com/v3/ai_optimization/claude/llm_responses/tasks_ready/) list. The error code and message depend on your server’s configuration.

See [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) to learn more about using pingbacks and postbacks with DataForSEO APIs.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `user_prompt` | string | *prompt for the AI model***required field**the question or task you want to send to the AI model;you can specify **up to 500 characters** in the `user_prompt` field |
| `model_name` | string | *name of the AI model***required field**`model_name`consists of the actual model name and version name;if the basic model name is specified, its latest version will be set by default;for example, if `claude-opus-4-0` is specified, the `claude-opus-4-20250514` will be set as `model_name` automatically;you can receive the list of available LLM models by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/claude/llm_responses/models](https://api.dataforseo.com/v3/ai_optimization/claude/llm_responses/models)` |
| `max_output_tokens` | integer | *maximum number of tokens in the AI response*optional fieldminimum value: `1`;maximum value: `4096`;default value: `2048`;**Note:** if `web_search` is set to `true` or the reasoning model is specified in the request, the output token count may exceed the specified `max_output_tokens` limit**Note #2:** if `use_reasoning` is set to `true`, the minimum value for `max_output_tokens` is `1025` |
| `temperature` | float | *randomness of the AI response*optional fieldhigher values make output more diverse; lower values make output more focused;minimum value: `0`maximum value: `1`default value: `0.7`**Note:** `temperature` cannot be used together with `top_p` in the same request |
| `top_p` | float | *diversity of the AI response*optional field controls diversity of the response by limiting token selection;minimum value: `0`maximum value: `1` default value: `null`**Note:** `top_p` cannot be used together with `temperature` in the same request |
| `web_search` | boolean | *enable web search for current information*optional fieldwhen enabled, the AI model can access and cite current web information;**Note:** refer to the [Models endpoint](https://docs.dataforseo.com/v3/ai_optimization/claude/llm_responses/models/) for a list of models that support `web_search`; default value: `false`;The cost of the parameter can be calculated on the [Pricing](https://docs.anthropic.com/en/docs/about-claude/pricing) page |
| `force_web_search` | boolean | *force AI agent to use web search*optional fieldto enable this parameter, `web_search` must also be enabled;when enabled, the AI model is forced to access and cite current web information;default value: `false`;**Note:** even if the parameter is set to `true`, there is no guarantee web sources will be cited in the response |
| `web_search_country_iso_code` | string | *ISO country code of the location used for searching the web*optional fieldpossible values: `'AR','AT','AU','BE','BR','CA','CH','CL','CN','DE','DK','ES','FI','FR','GB','HK','ID','IN','IT','JP','KR','MX','MY','NL','NO','NZ','PH','PL','PT','RU','SA','SE','TR','TW','US','ZA'` |
| `web_search_city` | string | *city name of the location used for searching the web*optional field |
| `system_message` | string | *instructions for the AI behaviour*optional fielddefines the AI's role, tone, or specific behavior;you can specify **up to 500 characters** in the `system_message` field |
| `message_chain` | array | *conversation history*optional fieldarray of message objects representing previous conversation turns;each object must contain `role` and `message` parameters:`role` string with either `user` or `ai` role;`message` string with message content (max 500 characters);you can specify ** the maximum of 10 message objects** in the array;example:`"message_chain": [{"role":"user","message":"Hello, what’s up?"},{"role":"ai","message":"Hello! I’m doing well, thank you. How can I assist you today?"}]` |
| `use_reasoning` | boolean | *enable reasoning for the AI model*optional fieldwhen enabled, the model will perform reasoning before generating a responserefer to the [Models endpoint](https://docs.dataforseo.com/v3/ai_optimization/claude/llm_responses/models/) for a list of models that support `reasoning`default value: `false`**Note:** if set to `true`, the minimum value for `max_output_tokens` is `1025`**Note #2:** if set to `true`, `force_web_search` must be set to `false`**Note #3:** if set to `true`, the `temperature` and `top_p` cannot be used |
| `tag` | string | *user-defined task identifier*optional field*the character limit is 255*you can use this parameter to identify the task and match it with the resultyou will find the specified `tag` value in the `data` object of the response |
| `postback_url` | string | *URL for sending task results*optional fieldonce the task is completed, we will send a POST request with its results compressed in the `gzip` format to the `postback_url` you specifiedyou can use the ‘$id’ string as a `$id` variable and ‘$tag’ as urlencoded `$tag` variable. We will set the necessary values before sending the request.example:`[http://your-server.com/postbackscript?id=$id](http://your-server.com/postbackscript?id=$id)``[http://your-server.com/postbackscript?id=$id&tag=$tag](http://your-server.com/postbackscript?id=$id&tag=$tag)`**Note:** special character in `postback_url` will be urlencoded;i.a., the `#` character will be encoded into `%23`learn more on our [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) |
| `pingback_url` | string | *notification URL of a completed task*optional fieldwhen a task is completed we will notify you by GET request sent to the URL you have specifiedyou can use the ‘$id’ string as a `$id` variable and ‘$tag’ as urlencoded `$tag` variable. We will set the necessary values before sending the requestexample:`[http://your-server.com/pingscript?id=$id](http://your-server.com/pingscript?id=$id)``[http://your-server.com/pingscript?id=$id&tag=$tag](http://your-server.com/pingscript?id=$id&tag=$tag)`**Note:** special character in `pingback_url` will be urlencoded;i.a., the `#` character will be encoded into `%23`learn more on our [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)<br>**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total tasks cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`**array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *unique task identifier in our system*<br>**unique task identifier in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task *<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| ** `result`** | array | *array of results*<br>in this case, the value will be `null` |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Tasks Ready
*Source: [https://docs.dataforseo.com/v3/ai_optimization/claude/llm_responses/tasks_ready/](https://docs.dataforseo.com/v3/ai_optimization/claude/llm_responses/tasks_ready/)*
#### Get Claude LLM Responses Completed Tasks

This endpoint is designed to provide you with a list of completed tasks, which haven’t been collected yet. If you use the Standard method without specifying the `postback_url`, you can receive the list of `id` for all completed tasks using this endpoint. Then, you can collect the results using the **‘Task GET’** endpoint.

Learn more about task completion and obtaining a list of completed tasks in [this help center article.](https://dataforseo.com/help-center/completed-tasks)

Tasks using the Standard method **may take up to 72 hours to complete**. If the task is not completed within this time, it is marked as failed, and the $0.01 advance is refunded. It is also important to note that if your account balance is negative, you will not receive the results even if the task is completed successfully.

**Note:** due to the peculiarities of our architecture the queue of completed tasks is updated with a small delay, which can be an issue for high-volume users. If your system requires collecting over 1000 tasks a minute, we recommend using [pingbacks/postbacks](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) instead, and applying the Tasks Ready endpoint only to obtain the IDs of failed postback tasks.

GEThttps://api.dataforseo.com/v3/ai_optimization/claude/llm_responses/tasks_ready

Pricing

Your account will not be charged when receiving results

Each separate task will remain on the list until it is collected. You can make **up to 20 API calls per minute.** With each API call, you can get 1000 tasks completed within three previous days. The list will not contain the tasks which have already been collected and the tasks that were not collected **within the three days** after completion.

Please note that if you specify the `postback_url`, the task will not be in the list of completed tasks. The task can only be found in the list if the request to your server failed, and your server returned HTTP code response less than `200` or higher than `300`.

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total *tasks* cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier***unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*generated by DataForSEO; can be within the following range: 10000-60000you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the parameters passed in the request's URL* |
| **`result`** | array | *array of results* |
| `id` | string | *task identifier of the completed task***unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `se` | string | *LLM model specified when setting the task* |
| `function` | string | *type of the task* |
| `date_posted` | string | *date when the task was posted (in the UTC format)* |
| `tag` | string | *user-defined task identifier* |
| `endpoint` | string | *URL for collecting the results of the task* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Task GET
*Source: [https://docs.dataforseo.com/v3/ai_optimization/claude/llm_responses/task_get/](https://docs.dataforseo.com/v3/ai_optimization/claude/llm_responses/task_get/)*
#### Get Claude LLM Responses Results by id

Claude LLM Responses endpoint allows you to retrieve structured responses from a specific Claude model, based on the input parameters.

Tasks using the Standard method **may take up to 72 hours to complete**. If the task is not completed within this time, it is marked as failed, and the $0.01 advance is refunded. It is also important to note that if your account balance is negative, you will not receive the results even if the task is completed successfully.

GEThttps://api.dataforseo.com/v3/ai_optimization/claude/llm_responses/task_get/$id

Pricing

Your account will be charged only for posting a task. You can get the results of the task within the next 30 days for free.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/ai-optimization/llm-responses) page.

**Description of the fields for sending a request:**

| Field name | Type | Description |
| --- | --- | --- |
| `id` | string | *task identifier***unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format**you will be able to use it within **30 days** to request the results of the task at any time |

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
| `status_code` | integer | *status code of the task*generated by DataForSEO; can be within the following range: 10000-60000you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD*includes the base task price plus the `money_spent` value |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `model_name` | string | *name of the AI model used* |
| `input_tokens` | integer | *number of tokens in the input*total count of tokens processed |
| `output_tokens` | integer | *number of tokens in the output*total count of tokens generated in the AI response |
| `reasoning_tokens` | integer | *number of reasoning tokens*total count of tokens used to generate reasoning content |
| `web_search` | boolean | *indicates if web search was used* |
| `money_spent` | float | *cost of AI tokens, USD*the price charged by the third-party AI model provider for according to its [Pricing](https://docs.anthropic.com/en/docs/about-claude/pricing) |
| `datetime` | string | *date and time when the result was received*in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”example:`2019-11-15 12:57:46 +00:00` |
| **`items`** | array | *array of response items*contains structured AI response data |
| **`reasoning`** | object | *element in the response* |
| `type` | string | *type of the element = **'reasoning'*****Note:** this element is supported only in reasoning models and is not guaranteed to be returned |
| **`sections`** | array | *reasoning chain sections*array of objects containing the reasoning chain sections generated by the LLM |
| `type` | string | *type of element*=***'summary_text'*** |
| `text` | string | *text of the reasoning chain section*text of the reasoning chain section summarizing the model's thought process |
| **`message`** | object | *element in the response* |
| `type` | string | *type of the element = **'message'*** |
| **`sections`** | array | *array of content sections*contains different parts of the AI response |
| `type` | string | *type of element*=***'text'*** |
| `text` | string | *AI-generated text content* |
| **`annotations`** | array | *array of references used to generate the response*equals `null` if the `web_search` parameter is not set to `true`**Note:** `annotations` may return empty even when `web_search` is `true`, as the AI will attempt to retrieve web information but may not find relevant results |
| `title` | string | *the domain name or title of the quoted source* |
| `url` | string | *URL of the quoted source* |
| `fan_out_queries` | array | *array of fan-out queries*contains related search queries derived from the main query to provide a more comprehensive response |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Live
*Source: [https://docs.dataforseo.com/v3/ai_optimization/claude/llm_responses/live/](https://docs.dataforseo.com/v3/ai_optimization/claude/llm_responses/live/)*
#### Live Claude LLM Responses

Live Claude LLM Responses endpoint allows you to retrieve structured responses from a specific Claude model, based on the input parameters.

POSThttps://api.dataforseo.com/v3/ai_optimization/claude/llm_responses/live

Pricing

The cost of the task can be calculated on the [Pricing page](https://dataforseo.com/pricing/ai-optimization/llm-responses).

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute, each Live Claude LLM Responses call can contain only one task.

**The number of concurrent Live tasks is currently limited to 30 per account for each platform in the LLM Responses.**

**Execution time for tasks set with the Live Claude LLM Responses endpoint is currently up to 120 seconds.**

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `user_prompt` | string | *prompt for the AI model***required field**the question or task you want to send to the AI model;you can specify **up to 500 characters** in the `user_prompt` field |
| `model_name` | string | *name of the AI model***required field**`model_name`consists of the actual model name and version name;if the basic model name is specified, its latest version will be set by default;for example, if `claude-opus-4-0` is specified, the `claude-opus-4-20250514` will be set as `model_name` automatically;you can receive the list of available LLM models by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/claude/llm_responses/models](https://api.dataforseo.com/v3/ai_optimization/claude/llm_responses/models)` |
| `max_output_tokens` | integer | *maximum number of tokens in the AI response*optional fieldminimum value: `1`;maximum value: `4096`;default value: `2048`;**Note:** if `web_search` is set to `true` or the reasoning model is specified in the request, the output token count may exceed the specified `max_output_tokens` limit**Note #2:** if `use_reasoning` is set to `true`, the minimum value for `max_output_tokens` is `1025` |
| `temperature` | float | *randomness of the AI response*optional fieldhigher values make output more diverse; lower values make output more focused;minimum value: `0`maximum value: `1`default value: `0.7`**Note:** `temperature` cannot be used together with `top_p` in the same request |
| `top_p` | float | *diversity of the AI response*optional field controls diversity of the response by limiting token selection;minimum value: `0`maximum value: `1` default value: `null`**Note:** `top_p` cannot be used together with `temperature` in the same request |
| `web_search` | boolean | *enable web search for current information*optional fieldwhen enabled, the AI model can access and cite current web information;**Note:** refer to the [Models endpoint](https://docs.dataforseo.com/v3/ai_optimization/claude/llm_responses/models/) for a list of models that support `web_search`; default value: `false`;The cost of the parameter can be calculated on the [Pricing](https://docs.anthropic.com/en/docs/about-claude/pricing) page |
| `force_web_search` | boolean | *force AI agent to use web search*optional fieldto enable this parameter, `web_search` must also be enabled;when enabled, the AI model is forced to access and cite current web information;default value: `false`;**Note:** even if the parameter is set to `true`, there is no guarantee web sources will be cited in the response |
| `web_search_country_iso_code` | string | *ISO country code of the location used for searching the web*optional fieldpossible values: `'AR','AT','AU','BE','BR','CA','CH','CL','CN','DE','DK','ES','FI','FR','GB','HK','ID','IN','IT','JP','KR','MX','MY','NL','NO','NZ','PH','PL','PT','RU','SA','SE','TR','TW','US','ZA'` |
| `web_search_city` | string | *city name of the location used for searching the web*optional field |
| `system_message` | string | *instructions for the AI behaviour*optional fielddefines the AI's role, tone, or specific behavior;you can specify **up to 500 characters** in the `system_message` field |
| `message_chain` | array | *conversation history*optional fieldarray of message objects representing previous conversation turns;each object must contain `role` and `message` parameters:`role` string with either `user` or `ai` role;`message` string with message content (max 500 characters);you can specify ** the maximum of 10 message objects** in the array;example:`"message_chain": [{"role":"user","message":"Hello, what’s up?"},{"role":"ai","message":"Hello! I’m doing well, thank you. How can I assist you today?"}]` |
| `use_reasoning` | boolean | *enable reasoning for the AI model*optional fieldwhen enabled, the model will perform reasoning before generating a responserefer to the [Models endpoint](https://docs.dataforseo.com/v3/ai_optimization/claude/llm_responses/models/) for a list of models that support `reasoning`default value: `false`**Note:** if set to `true`, the minimum value for `max_output_tokens` is `1025`**Note #2:** if set to `true`, `force_web_search` must be set to `false`**Note #3:** if set to `true`, the `temperature` and `top_p` cannot be used |
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
| `status_code` | integer | *status code of the task*generated by DataForSEO; can be within the following range: 10000-60000you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD*includes the base task price plus the `money_spent` value |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `model_name` | string | *name of the AI model used* |
| `input_tokens` | integer | *number of tokens in the input*total count of tokens processed |
| `output_tokens` | integer | *number of tokens in the output*total count of tokens generated in the AI response |
| `reasoning_tokens` | integer | *number of reasoning tokens*total count of tokens used to generate reasoning content |
| `web_search` | boolean | *indicates if web search was used* |
| `money_spent` | float | *cost of AI tokens, USD*the price charged by the third-party AI model provider for according to its [Pricing](https://docs.anthropic.com/en/docs/about-claude/pricing) |
| `datetime` | string | *date and time when the result was received*in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”example:`2019-11-15 12:57:46 +00:00` |
| **`items`** | array | *array of response items*contains structured AI response data |
| **`reasoning`** | object | element in the response |
| `type` | string | *type of the element = **'reasoning'*****Note:** this element is supported only in reasoning models and is not guaranteed to be returned |
| **`sections`** | array | *reasoning chain sections*array of objects containing the reasoning chain sections generated by the LLM |
| `type` | string | *type of element*=***'summary_text'*** |
| `text` | string | *text of the reasoning chain section*text of the reasoning chain section summarizing the model's thought process |
| **`message`** | object | element in the response |
| `type` | string | *type of the element = **'message'*** |
| **`sections`** | array | *array of content sections*contains different parts of the AI response |
| `type` | string | *type of element*=***'text'*** |
| `text` | string | *AI-generated text content* |
| **`annotations`** | array | *array of references used to generate the response*equals `null` if the `web_search` parameter is not set to `true`**Note:** `annotations` may return empty even when `web_search` is `true`, as the AI will attempt to retrieve web information but may not find relevant results |
| `title` | string | *the domain name or title of the quoted source* |
| `url` | string | *URL of the quoted source* |
| `fan_out_queries` | array | *array of fan-out queries*contains related search queries derived from the main query to provide a more comprehensive response |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Overview
*Source: [https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_responses/overview/](https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_responses/overview/)*
### Gemini LLM Responses: Overview

This API allows you to generate and retrieve structured Gemini responses

Gemini LLM Responses API enables generation of structured responses from Gemini, based on your specified input parameters. You can use this API to discover how Gemini responds to queries about your brand, product, competitors, or any other target keywords and topics.

The endpoints of this API include:

• [Gemini LLM Responses endpoint](https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_responses/live/) retrieves structured responses from a specific Gemini AI model, based on your input parameters.

• [Gemini Models LLM Responses endpoint](https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_responses/models/) provides a list of available Gemini AI models you can use with Gemini LLM Responses endpoint.

To find answers on common questions about AI Optimization API and find guidance on most efficient use, [visit our Help Center.](https://dataforseo.com/help-center/category/ai-optimization-api)

##### Methods

The cost of using Gemini LLM Responses API depends on the selected method and priority of task execution. Available methods and priorities are described below.

DataForSEO has two main methods to deliver the results: Standard and Live.

If your system requires delivering instant results, **the Live method** is the best solution for you. Unlike the Standard method, this method doesn’t require making separate POST and GET requests to the corresponding endpoints.

If you don’t need to receive data in real-time, you can use **the Standard method** of data retrieval. This method requires making separate POST and GET requests, but it’s more affordable. Using this method, you can retrieve the results after our system collects them.

Alternatively, you can specify `pingback_url` or `postback_url` when setting a task, and we will notify you on completion of tasks or send them to you respectively.

If you need to set several tasks, you can receive the list of id for all completed tasks using **‘Tasks Ready’** endpoint, and then collect the results of each separate task using **‘Task GET’** endpoint.

You can send up to 2000 API calls per minute. Contact us if you would like to raise the limit. Note that the maximum number of Live requests that can be sent simultaneously **is limited to 30** per account for each platform in the LLM Responses.

Execution time for tasks set using [the Live method](https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_responses/live/) is currently **up to 120 seconds**. Tasks set using [the Standard method](https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_responses/task_post/) **may take up to 72 hours to complete**.

##### Cost

The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/ai-optimization/llm-responses) page. You can check your spending in your [account dashboard](https://app.dataforseo.com/api-access) or by making a separate call to [the User Data endpoint](https://docs.dataforseo.com/v3/appendix/user_data/?php)

You can test Gemini LLM Responses API for free using DataForSEO [Sandbox.](https://docs.dataforseo.com/v3/appendix/sandbox/)

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

---


##### Models
*Source: [https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_responses/models/](https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_responses/models/)*
#### Gemini LLM Responses Models List

Pricing

Your account will not be charged for using this API

GEThttps://api.dataforseo.com/v3/ai_optimization/gemini/llm_responses/models

You will receive the list of available Gemini AI models by calling this API.
 
As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *general informational message*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total tasks cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier***unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*generated by DataForSEO; can be within the following range: 10000-60000you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the parameters passed in the URL of the GET request* |
| **`result`** | array | *array of results* |
| `model_name` | string | *name of the AI model* |
| `reasoning` | boolean | *indicates if the AI model supports reasoning* |
| `web_search_supported` | boolean | *web search support for the AI model*if `true`, the `web_search` parameter can be set with the AI model |
| `task_post_supported` | boolean | *indicates if Standard (POST-GET) data retrieval is supported*if `true`, you can use the [Standard (POST-GET)](https://dataforseo.com/help-center/live-vs-standard-method) data retrieval method with the AI model |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Task POST
*Source: [https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_responses/task_post/](https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_responses/task_post/)*
#### Setting Gemini LLM Responses Tasks

Gemini LLM Responses endpoint allows you to retrieve structured responses from a specific Gemini model, based on the input parameters.

This is the Standard method of data retrieval. If you don’t need to receive data in real-time, this method is the best option for you. Set a task and retrieve the results when our system collects them. Execution time depends on the system workload.

If your system requires delivering instant results, [the Live method](https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_responses/live/) will be a better solution. This method doesn’t require making separate POST and GET requests to the corresponding endpoints.

Note that this endpoint requires making an automatic prepayment of $0.01 to execute the task. If the cost charged by the LLM is less than $0.01, the difference will be refunded to your account balance.

POSThttps://api.dataforseo.com/v3/ai_optimization/gemini/llm_responses/task_post

Pricing

Your account will be charged only for setting a task.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/ai-optimization/llm-responses) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). Task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute, with each POST call containing no more than 100 tasks. If your POST call contains over 100 tasks, the tasks over this limit will return the `40006` error.

Tasks using the Standard method **may take up to 72 hours to complete**. If the task is not completed within this time, it is marked as failed, and the $0.01 advance is refunded. It is also important to note that if your account balance is negative, you will not receive the results even if the task is completed successfully.

You can also retrieve the results of completed tasks using the unique task identifier `id`. Alternatively, we can send them to you as soon as they are ready if you specify the `postback_url` or `pingback_url` when setting a task. Note that if your server doesn’t respond within 10 seconds, the connection will be aborted by timeout, and the task will be transferred to the [tasks_ready](https://docs.dataforseo.com/v3/keywords_data/google_ads/search_volume/tasks_ready/?php) list. The error code and message depend on your server’s configuration.

See [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) to learn more about using pingbacks and postbacks with DataForSEO APIs.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `user_prompt` | string | *prompt for the AI model***required field**the question or task you want to send to the AI model;you can specify **up to 500 characters** in the `user_prompt` field |
| `model_name` | string | *name of the AI model***required field**`model_name`consists of the actual model name and version name;if the basic model name is specified, its latest version will be set by default;for example, if `gemini-1.5-pro` is specified, the `gemini-1.5-pro-002` will be set as `model_name` automatically;you can receive the list of available LLM models by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/gemini/llm_responses/models](https://api.dataforseo.com/v3/ai_optimization/gemini/llm_responses/models)` |
| `max_output_tokens` | integer | *maximum number of tokens in the AI response*optional fieldminimum value: `1`;maximum value: `4096`;default value: `2048`;**Note:** if `web_search` is set to `true` or the reasoning model is specified in the request, the output token count may exceed the specified `max_output_tokens` limit**Note #2:** if `use_reasoning` is set to `true`, the minimum value for `max_output_tokens` is `1024` |
| `temperature` | float | *randomness of the AI response*optional fieldhigher values make output more diverse lower values make output more focusedminimum value: `0`maximum value: `2`default value: `1.3` |
| `top_p` | float | *diversity of the AI response*optional field controls diversity of the response by limiting token selectionminimum value: `0`maximum value: `1` default value: `0.9` |
| `web_search` | boolean | *enable web search for current information*optional fieldwhen enabled, the AI model can access and cite current web information;**Note:** refer to the [Models endpoint](https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_responses/models/) for a list of models that support `web_search`; default value: `false`;The cost of the parameter can be calculated on the [Pricing](https://ai.google.dev/gemini-api/docs/pricing) page |
| `system_message` | string | *instructions for the AI behavior*optional fielddefines the AI's role, tone, or specific behavior you can specify **up to 500 characters** in the `system_message` field |
| `message_chain` | array | *conversation history*optional fieldarray of message objects representing previous conversation turns;each object must contain `role` and `message` parameters:`role` string with either `user` or `ai` role;`message` string with message content (max 500 characters);you can specify ** the maximum of 10 message objects** in the array;example:`"message_chain": [{"role":"user","message":"Hello, what’s up?"},{"role":"ai","message":"Hello! I’m doing well, thank you. How can I assist you today?"}]` |
| `use_reasoning` | boolean | *enable reasoning for the AI model*optional fieldwhen enabled, the model will perform reasoning before generating a responserefer to the [Models endpoint](https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_responses/models/) for a list of models that support `reasoning`default value: `false`**Note:** if set to `true`, the minimum value for `max_output_tokens` is `1024`**Note #2:** for Gemini Pro models, the `use_reasoning` will automatically be set to `true` |
| `tag` | string | *user-defined task identifier*optional field*the character limit is 255*you can use this parameter to identify the task and match it with the resultyou will find the specified `tag` value in the `data` object of the response |
| `postback_url` | string | *URL for sending task results*optional fieldonce the task is completed, we will send a POST request with its results compressed in the `gzip` format to the `postback_url` you specifiedyou can use the ‘$id’ string as a `$id` variable and ‘$tag’ as urlencoded `$tag` variable. We will set the necessary values before sending the request.example:`[http://your-server.com/postbackscript?id=$id](http://your-server.com/postbackscript?id=$id)``[http://your-server.com/postbackscript?id=$id&tag=$tag](http://your-server.com/postbackscript?id=$id&tag=$tag)`**Note:** special character in `postback_url` will be urlencoded;i.a., the `#` character will be encoded into `%23`learn more on our [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) |
| `pingback_url` | string | *notification URL of a completed task*optional fieldwhen a task is completed we will notify you by GET request sent to the URL you have specifiedyou can use the ‘$id’ string as a `$id` variable and ‘$tag’ as urlencoded `$tag` variable. We will set the necessary values before sending the requestexample:`[http://your-server.com/pingscript?id=$id](http://your-server.com/pingscript?id=$id)``[http://your-server.com/pingscript?id=$id&tag=$tag](http://your-server.com/pingscript?id=$id&tag=$tag)`**Note:** special character in `pingback_url` will be urlencoded;i.a., the `#` character will be encoded into `%23`learn more on our [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)<br>**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total tasks cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`**array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *unique task identifier in our system*<br>**unique task identifier in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task *<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| ** `result`** | array | *array of results*<br>in this case, the value will be `null` |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Tasks Ready
*Source: [https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_responses/tasks_ready/](https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_responses/tasks_ready/)*
#### Get Gemini LLM Responses Completed Tasks

This endpoint is designed to provide you with a list of completed tasks, which haven’t been collected yet. If you use the Standard method without specifying the `postback_url`, you can receive the list of `id` for all completed tasks using this endpoint. Then, you can collect the results using the **‘Task GET’** endpoint.

Learn more about task completion and obtaining a list of completed tasks in [this help center article.](https://dataforseo.com/help-center/completed-tasks)

Tasks using the Standard method **may take up to 72 hours to complete**. If the task is not completed within this time, it is marked as failed, and the $0.01 advance is refunded. It is also important to note that if your account balance is negative, you will not receive the results even if the task is completed successfully.

**Note:** due to the peculiarities of our architecture the queue of completed tasks is updated with a small delay, which can be an issue for high-volume users. If your system requires collecting over 1000 tasks a minute, we recommend using [pingbacks/postbacks](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) instead, and applying the Tasks Ready endpoint only to obtain the IDs of failed postback tasks.

GEThttps://api.dataforseo.com/v3/ai_optimization/gemini/llm_responses/tasks_ready

Pricing

Your account will not be charged when receiving results

Each separate task will remain on the list until it is collected. You can make **up to 20 API calls per minute.** With each API call, you can get 1000 tasks completed within three previous days. The list will not contain the tasks which have already been collected and the tasks that were not collected **within the three days** after completion.

Please note that if you specify the `postback_url`, the task will not be in the list of completed tasks. The task can only be found in the list if the request to your server failed, and your server returned HTTP code response less than `200` or higher than `300`.

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total *tasks* cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier***unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*generated by DataForSEO; can be within the following range: 10000-60000you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the parameters passed in the request's URL* |
| **`result`** | array | *array of results* |
| `id` | string | *task identifier of the completed task***unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `se` | string | *LLM model specified when setting the task* |
| `function` | string | *type of the task* |
| `date_posted` | string | *date when the task was posted (in the UTC format)* |
| `tag` | string | *user-defined task identifier* |
| `endpoint` | string | *URL for collecting the results of the task* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Task GET
*Source: [https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_responses/task_get/](https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_responses/task_get/)*
#### Get Gemini LLM Responses Results by id

Gemini LLM Responses endpoint allows you to retrieve structured responses from a specific Gemini model, based on the input parameters.

Tasks using the Standard method **may take up to 72 hours to complete**. If the task is not completed within this time, it is marked as failed, and the $0.01 advance is refunded. It is also important to note that if your account balance is negative, you will not receive the results even if the task is completed successfully.

GEThttps://api.dataforseo.com/v3/ai_optimization/gemini/llm_responses/task_get/$id

Pricing

Your account will be charged only for posting a task. You can get the results of the task within the next 30 days for free.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/ai-optimization/llm-responses) page.

**Description of the fields for sending a request:**

| Field name | Type | Description |
| --- | --- | --- |
| `id` | string | *task identifier***unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format**you will be able to use it within **30 days** to request the results of the task at any time |

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
| `status_code` | integer | *status code of the task*generated by DataForSEO; can be within the following range: 10000-60000you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD*includes the base task price plus the `money_spent` value |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `model_name` | string | *name of the AI model used* |
| `input_tokens` | integer | *number of tokens in the input*total count of tokens processed |
| `output_tokens` | integer | *number of tokens in the output*total count of tokens generated in the AI response |
| `reasoning_tokens` | integer | *number of reasoning tokens*total count of tokens used to generate reasoning content |
| `web_search` | boolean | *indicates if web search was used* |
| `money_spent` | float | *cost of AI tokens, USD*the price charged by the third-party AI model provider for according to its [Pricing](https://platform.openai.com/docs/pricing) |
| `datetime` | string | *date and time when the result was received*in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”example:`2019-11-15 12:57:46 +00:00` |
| `items` | array | *array of response items*contains structured AI response data |
| **`items`** | array | *array of response items*contains structured AI response data |
| **`reasoning`** | object | *element in the response* |
| `type` | string | *type of the element = **'reasoning'*****Note:** this element is supported only in reasoning models and is not guaranteed to be returned |
| **`sections`** | array | *reasoning chain sections*array of objects containing the reasoning chain sections generated by the LLM |
| `type` | string | *type of element*=***'summary_text'*** |
| `text` | string | *text of the reasoning chain section*text of the reasoning chain section summarizing the model's thought process |
| **`message`** | object | *element in the response* |
| `type` | string | *type of the element = **'message'*** |
| **`sections`** | array | *array of content sections*contains different parts of the AI response |
| `type` | string | *type of element*=***'text'*** |
| `text` | string | *AI-generated text content* |
| **`annotations`** | array | *array of references used to generate the response*equals `null` if the `web_search` parameter is not set to `true`**Note:** `annotations` may return empty even when `web_search` is `true`, as the AI will attempt to retrieve web information but may not find relevant results |
| `title` | string | *the domain name or title of the quoted source* |
| `url` | string | *redirect URL to the quoted source*contains a Vertex AI redirect that leads to the original source |
| `fan_out_queries` | array | *array of fan-out queries*contains related search queries derived from the main query to provide a more comprehensive response |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Live
*Source: [https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_responses/live/](https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_responses/live/)*
#### Live Gemini LLM Responses

Live Gemini LLM Responses endpoint allows you to retrieve structured responses from a specific Gemini AI model, based on the input parameters.

POSThttps://api.dataforseo.com/v3/ai_optimization/gemini/llm_responses/live

Pricing

The cost of the task can be calculated on the [Pricing page](https://dataforseo.com/pricing/ai-optimization/llm-responses).

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute, each Live Gemini LLM Responses call can contain only one task.

**The number of concurrent Live tasks is currently limited to 30 per account for each platform in the LLM Responses.**

**Execution time for tasks set with the Live Gemini LLM Responses endpoint is currently up to 120 seconds.**

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `user_prompt` | string | *prompt for the AI model***required field**the question or task you want to send to the AI model;you can specify **up to 500 characters** in the `user_prompt` field |
| `model_name` | string | *name of the AI model***required field**`model_name`consists of the actual model name and version name;if the basic model name is specified, its latest version will be set by default;for example, if `gemini-1.5-pro` is specified, the `gemini-1.5-pro-002` will be set as `model_name` automatically;you can receive the list of available LLM models by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/gemini/llm_responses/models](https://api.dataforseo.com/v3/ai_optimization/gemini/llm_responses/models)` |
| `max_output_tokens` | integer | *maximum number of tokens in the AI response*optional fieldminimum value: `1`maximum value: `4096`;default value: `2048`;**Note:** if `web_search` is set to `true` or the reasoning model is specified in the request, the output token count may exceed the specified `max_output_tokens` limit**Note #2:** if `use_reasoning` is set to `true`, the minimum value for `max_output_tokens` is `1024` |
| `temperature` | float | *randomness of the AI response*optional fieldhigher values make output more diverse lower values make output more focusedminimum value: `0`maximum value: `2`default value: `1.3` |
| `top_p` | float | *diversity of the AI response*optional field controls diversity of the response by limiting token selectionminimum value: `0`maximum value: `1` default value: `0.9` |
| `web_search` | boolean | *enable web search for current information*optional fieldwhen enabled, the AI model can access and cite current web information;**Note:** refer to the [Models endpoint](https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_responses/models/) for a list of models that support `web_search`; default value: `false`;The cost of the parameter can be calculated on the [Pricing](https://ai.google.dev/gemini-api/docs/pricing) page |
| `system_message` | string | *instructions for the AI behavior*optional fielddefines the AI's role, tone, or specific behavior you can specify **up to 500 characters** in the `system_message` field |
| `message_chain` | array | *conversation history*optional fieldarray of message objects representing previous conversation turns;each object must contain `role` and `message` parameters:`role` string with either `user` or `ai` role;`message` string with message content (max 500 characters);you can specify ** the maximum of 10 message objects** in the array;example:`"message_chain": [{"role":"user","message":"Hello, what’s up?"},{"role":"ai","message":"Hello! I’m doing well, thank you. How can I assist you today?"}]` |
| `use_reasoning` | boolean | *enable reasoning for the AI model*optional fieldwhen enabled, the model will perform reasoning before generating a responserefer to the [Models endpoint](https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_responses/models/) for a list of models that support `reasoning`default value: `false`**Note:** if set to `true`, the minimum value for `max_output_tokens` is `1024`**Note #2:** for Gemini Pro models, the `use_reasoning` will automatically be set to `true` |
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
| `status_code` | integer | *status code of the task*generated by DataForSEO; can be within the following range: 10000-60000you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD*includes the base task price plus the `money_spent` value |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `model_name` | string | *name of the AI model used* |
| `input_tokens` | integer | *number of tokens in the input*total count of tokens processed |
| `output_tokens` | integer | *number of tokens in the output*total count of tokens generated in the AI response |
| `reasoning_tokens` | integer | *number of reasoning tokens*total count of tokens used to generate reasoning content |
| `web_search` | boolean | *indicates if web search was used* |
| `money_spent` | float | *cost of AI tokens, USD*the price charged by the third-party AI model provider for according to its [Pricing](https://ai.google.dev/gemini-api/docs/pricing) |
| `datetime` | string | *date and time when the result was received*in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”example:`2019-11-15 12:57:46 +00:00` |
| **`items`** | array | *array of response items*contains structured AI response data |
| **`reasoning`** | object | *element in the response* |
| `type` | string | *type of the element = **'reasoning'*****Note:** this element is supported only in reasoning models and is not guaranteed to be returned |
| **`sections`** | array | *reasoning chain sections*array of objects containing the reasoning chain sections generated by the LLM |
| `type` | string | *type of element*=***'summary_text'*** |
| `text` | string | *text of the reasoning chain section*text of the reasoning chain section summarizing the model's thought process |
| **`message`** | object | *element in the response* |
| `type` | string | *type of the element = **'message'*** |
| **`sections`** | array | *array of content sections*contains different parts of the AI response |
| `type` | string | *type of element*=***'text'*** |
| `text` | string | *AI-generated text content* |
| **`annotations`** | array | *array of references used to generate the response*equals `null` if the `web_search` parameter is not set to `true`**Note:** `annotations` may return empty even when `web_search` is `true`, as the AI will attempt to retrieve web information but may not find relevant results |
| `title` | string | *the domain name or title of the quoted source* |
| `url` | string | *redirect URL to the quoted source*contains a Vertex AI redirect that leads to the original source |
| `fan_out_queries` | array | *array of fan-out queries*contains related search queries derived from the main query to provide a more comprehensive response |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Overview
*Source: [https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/overview/](https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/overview/)*
### Gemini LLM Scraper: Overview

This API provides structured results from Gemini

Gemini LLM Scraper API allows you to retrieve structured and detailed results from Gemini, based on the keyword and other input paramaters. You can use this API to understand how Gemini responds to specific search queries, explore which sources and brands it quotes in its responses.

##### Gemini LLM Scraper functions

• [Gemini LLM Scraper Advanced endpoint](https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/live/advanced/) provides results from Gemini, based on specified keyword and other input parameters.

• [Gemini LLM Scraper HTML endpoint](https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/live/html/) provides a raw HTML page of Gemini results for the specified keyword, search engine, and location.

To find answers on common questions about DataForSEO APIs and find guidance on most efficient use, [visit our Help Center.](https://dataforseo.com/help-center/category/ai-optimization-api)

##### Methods

The cost of using Gemini LLM Scraper API depends on the selected method and priority of task execution. Available methods and priorities are described below.

DataForSEO has two main methods to deliver the results: Standard and Live.

If your system requires delivering instant results, **[the Live method](https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/live/advanced/)** is the best solution for you. Unlike the Standard method, this method doesn’t require making separate POST and GET requests to the corresponding endpoints.

If you don’t need to receive data in real-time, you can use **[the Standard method](https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/task_post/)** of data retrieval. This method requires making separate POST and GET requests, but it’s more affordable. Using this method, you can retrieve the results after our system collects them.

Alternatively, you can specify `pingback_url` or `postback_url` when setting a task, and we will notify you on completion of tasks or send them to you respectively.

If you need to set several tasks, you can receive the list of id for all completed tasks using **[‘Tasks Ready’](https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/tasks_ready/)** endpoint, and then collect the results of each separate task using **[‘Task GET’](https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/task_get/advanced/)** endpoint.

Learn more about task completion and obtaining a list of completed tasks in [this Help Center article](https://dataforseo.com/help-center/completed-tasks).

You can send up to 2000 API calls per minute. Contact us if you would like to raise the limit.

Execution time for tasks set with the [Live Gemini LLM Scraper endpoint](https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/live/advanced/) is currently **up to 120 seconds**.

##### Priorities and Cost

The Live method delivers results in real-time, and accordingly, the cost of requests made using this method will be the highest.

The Standard method has two different priorities that stand for the relative speed of task execution and have different prices:

1. Normal priority;
2. High priority.

The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/ai-optimization/llm-scraper) page. You can check your spending in your [account dashboard](https://app.dataforseo.com/api-access) or by making a separate call to [the User Data endpoint](https://docs.dataforseo.com/v3/appendix/user_data/?php)

You can test Gemini LLM Scraper API for free using DataForSEO [Sandbox.](https://docs.dataforseo.com/v3/appendix/sandbox/)

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

---


##### Locations
*Source: [https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/locations/](https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/locations/)*
#### Gemini LLM Scraper Locations List

Pricing

Your account will not be charged for using this API

GEThttps://api.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/locations

You will receive the list of locations by this API call. You can filter the list of locations by country when setting a task.

##### **Note:** All locations in Russia and Belarus are no longer supported across all DataForSEO services due to the invasion of Ukraine.

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *general informational message*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total tasks cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier***unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*generated by DataForSEO; can be within the following range: 10000-60000you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the parameters passed in the URL of the GET request* |
| **`result`** | array | *array of results* |
| `location_code` | integer | *location code* |
| `location_name` | string | *full name of the location* |
| `location_code_parent` | integer | *the code of the superordinate location*example:`"location_code": 9041134,"location_name": "Vienna International Airport,Lower Austria,Austria","location_code_parent": 20044`where `location_code_parent` corresponds to:`"location_code": 20044,"location_name": "Lower Austria,Austria"` |
| `country_iso_code` | string | *ISO country code of the location* |
| `location_type` | string | *location type* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Languages
*Source: [https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/languages/](https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/languages/)*
#### Gemini LLM Scraper Languages List

Pricing

Your account will not be charged for using this API

GEThttps://api.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/languages

You will receive the list of languages by calling this API.

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *general informational message*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total tasks cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier***unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*generated by DataForSEO; can be within the following range: 10000-60000you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the parameters passed in the URL of the GET request* |
| **`result`** | array | *array of results* |
| `language_name` | string | *language name* |
| `language_code` | string | *language code according to [ISO 639-1](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes)* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Task POST
*Source: [https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/task_post/](https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/task_post/)*
#### Setting Gemini LLM Scraper

Gemini LLM Scraper API provides structured results from Gemini. The results are specific to the selected location (see [the List of Locations](https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/locations/)) and language (see [the List of Languages](https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/languages/)), and keyword.

There are two different priorities that stand for the relative speed of task execution: normal and high.

POSThttps://api.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/task_post

Pricing

Your account will be charged only for setting a task.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/ai-optimization/llm-scraper) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute, with each POST call containing no more than 100 tasks. If your POST call contains over 100 tasks, the tasks over this limit will return the `40006` error.

You can retrieve the results of completed tasks using the unique task identifier `id`. Alternatively, we can send them to you as soon as they are ready if you specify the `postback_url` or `pingback_url` when setting a task. Note that if your server doesn’t respond within 10 seconds, the connection will be aborted by timeout, and the task will be transferred to the [‘Tasks Ready’](https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/tasks_ready/?php) list. The error code and message depend on your server’s configuration. ****

See [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) to learn more about using pingbacks and postbacks with DataForSEO APIs.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `keyword` | string | *keyword***required field**you can specify **up to 2000 characters** in the `keyword` fieldall %## will be decoded (plus character ‘+’ will be decoded to a space character)if you need to use the “%” character for your `keyword`, please specify it as “%25”;if you need to use the “+” character for your `keyword`, please specify it as “%2B”learn more about rules and limitations of `keyword` and `keywords` fields in DataForSEO APIs in this [Help Center article](https://dataforseo.com/help-center/rules-and-limitations-of-keyword-and-keywords-fields-in-dataforseo-apis) |
| `priority` | integer | *task priority*optional fieldcan take the following values:1 – normal execution priority (set by default)2 – high execution priorityYou will be additionally charged for the tasks with high execution priority.The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/ai-optimization/llm-scraper) page. |
| `location_name` | string | *full name of search engine location***required field if you don't specify** `location_code` or `location_coordinate`**if you use this field, you don't need to specify `location_code` or `location_coordinate`**you can receive the list of available locations of the search engine with their `location_name` by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/locations](https://api.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/locations)`example:`United States` |
| `location_code` | integer | *search engine location code***required field if you don't specify** `location_name` or `location_coordinate`**if you use this field, you don't need to specify `location_name` or `location_coordinate`**you can receive the list of available locations of the search engines with their `location_code` by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/locations](https://api.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/locations)`example:`2840` |
| `location_coordinate` | string | *GPS coordinates of a location***required field if you don't specify** `location_name` or `location_code`**if you use this field, you don't need to specify `location_name` or `location_code`**`location_coordinate` parameter should be specified in the *"latitude,longitude,radius"* formatthe maximum number of decimal digits for *"latitude"* and *"longitude"*: 7the minimum value for *"radius"*: 199 (mm)the maximum value for *"radius"*: 199999 (mm)example:`53.476225,-2.243572,200` |
| `language_name` | string | *full name of search engine language*required field if you don't specify `language_code`;if you use this field, you don't need to specify `language_code`;you can receive the list of available languages of the search engine with their `language_name` by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/languages](https://api.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/languages)`example:`English` |
| `language_code` | string | *search engine language code*required field if you don't specify `language_name`;if you use this field, you don't need to specify `language_name`;you can receive the list of available languages of the search engine with their `language_code`_by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/languages](https://api.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/languages)`example:`en` |
| `expand_citations` | boolean | *return expanded citation bar in HTML results*optional fieldwhen enabled, the HTML endpoint will return data from the expanded citation bar;default value: `false` |
| `tag` | string | *user-defined task identifier*optional field*the character limit is 255*you can use this parameter to identify the task and match it with the resultyou will find the specified `tag` value in the `data` object of the response |
| `postback_url` | string | *URL for sending task results*optional fieldonce the task is completed, we will send a POST request with its results compressed in the `gzip` format to the `postback_url` you specifiedyou can use the ‘$id’ string as a `$id` variable and ‘$tag’ as urlencoded `$tag` variable. We will set the necessary values before sending the request.example:`[http://your-server.com/postbackscript?id=$id](http://your-server.com/postbackscript?id=$id)``[http://your-server.com/postbackscript?id=$id&tag=$tag](http://your-server.com/postbackscript?id=$id&tag=$tag)`**Note:** special characters in `postback_url` will be urlencoded;i.a., the `#` character will be encoded into `%23`learn more on our [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) |
| `postback_data` | string | *postback_url datatype***required field if you specify `postback_url`**corresponds to the function you used for setting a taskpossible values:`advanced`, `html` |
| `pingback_url` | string | *notification URL of a completed task*optional fieldwhen a task is completed we will notify you by GET request sent to the URL you have specifiedyou can use the ‘$id’ string as a `$id` variable and ‘$tag’ as urlencoded `$tag` variable. We will set the necessary values before sending the request.example:`[http://your-server.com/pingscript?id=$id](http://your-server.com/pingscript?id=$id)``[http://your-server.com/pingscript?id=$id&tag=$tag](http://your-server.com/pingscript?id=$id&tag=$tag)`**Note:** special characters in `pingback_url` will be urlencoded;i.a., the `#` character will be encoded into `%23`learn more on our [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)<br>**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total tasks cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`**array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *unique task identifier in our system*<br>in the [Universally unique identifier (UUID)](https://en.wikipedia.org/wiki/Universally_unique_identifier) format |
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000 |
| `status_message` | string | *informational message of the task* |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| ** `result`** | array | *array of results*<br>in this case, the value will be `null` |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Tasks Ready
*Source: [https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/tasks_ready/](https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/tasks_ready/)*
#### Get Gemini LLM Scraper Completed Tasks

The **‘Tasks Ready’** endpoint is designed to provide you with the list of completed tasks, which haven’t been collected yet. If you use the Standard method without specifying the `postback_url`, you can receive the list of `id` for all completed tasks using this endpoint. Then, you can collect the results using the **‘Task GET’** endpoint.
Learn more about task completion and obtaining a list of completed tasks in [this help center article.](https://dataforseo.com/help-center/completed-tasks)

**Note:** due to the peculiarities of our architecture the queue of completed tasks is updated with a small delay, which can be an issue for high-volume users.

If your system requires collecting over 1000 tasks a minute, we recommend using [pingbacks/postbacks](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) instead, and applying the Tasks Ready endpoint only to obtain the IDs of failed postback tasks.

GEThttps://api.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/tasks_ready

Pricing

Your account will not be charged when receiving results

Each separate task will remain on the list until it is collected. You can make **up to 20 API calls per minute.** With each API call, you can get 1000 tasks completed within three previous days. The list will not contain the tasks which have already been collected and the tasks that were not collected **within three days** after completion.

Please note that if you specify the `postback_url`, the task will not be in the list of completed tasks. The task can only be found in the list if the request to your server failed, and your server returned HTTP code response less than `200` or higher than `300`.

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
| `status_code` | integer | *status code of the task*generated by DataForSEO; can be within the following range: 10000-60000you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the parameters passed in the request's URL* |
| **`result`** | array | *array of results* |
| `id` | string | *task identifier of the completed task***unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `se` | string | *search engine specified when setting the task* |
| `function` | string | *search engine function*example: `llm_scraper` |
| `date_posted` | string | *date when the task was posted (in the UTC format)* |
| `tag` | string | *user-defined task identifier* |
| `endpoint_advanced` | string | *URL for collecting the results of the Advanced task*if the Advanced function is not supported in the specified endpoint, the value will be `null` |
| `endpoint_html` | string | *URL for collecting the results of the HTML task*if the HTML function is not supported in the specified endpoint, the value will be `null` |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


###### Advanced
*Source: [https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/task_get/advanced/](https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/task_get/advanced/)*
#### Get Gemini LLM Scraper Advanced

GEThttps://api.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/task_get/advanced/$id

Pricing

Your account will be charged only for posting a task. You can get the results of the task within the next 30 days for free.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/ai-optimization/llm-scraper) page.

**Description of the fields for sending a request:**

| Field name | Type | Description |
| --- | --- | --- |
| `id` | string | *task identifier*[a universally unique identifier (UUID)](https://en.wikipedia.org/wiki/Universally_unique_identifier)**unique task identifier in our system**you will be able to use it within **30 days** to request the results of the task at any time |

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
| `status_code` | integer | *status code of the task*generated by DataForSEO; can be within the following range: 10000-60000you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `keyword` | string | *keyword received in a POST array***the keyword is returned with decoded %## (plus symbol '+' will be decoded to a space character)** |
| `location_code` | integer | *location code in a POST array* |
| `language_code` | string | *language code in a POST array* |
| `model` | string | *indicates the model version* |
| `datetime` | string | *date and time when the result was received*in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”example:`2019-11-15 12:57:46 +00:00` |
| `markdown` | string | *content of the element in markdown format*content of the result formatted in the [markdown markup language](https://en.wikipedia.org/wiki/Markdown) |
| **`sources`** | array | *array of sources*the sources the model actually cited or relied on in its final answer |
| `type` | string | *type of element*=***'gemini_source'*** |
| `title` | string | *source title* |
| `snippet` | string | *source description* |
| `domain` | string | *source domain* |
| `url` | string | *source URL* |
| `thumbnail` | string | *source thumbnail* |
| `source_name` | string | *source name* |
| `publication_date` | string | *date and time when the result was published*in the format: “year-month-date:minutes:UTC_difference_hours:UTC_difference_minutes”example:`2019-11-15 12:57:46 +00:00` |
| `markdown` | string | *content of the element in markdown format*content of the result formatted in the [markdown markup language](https://en.wikipedia.org/wiki/Markdown) |
| `se_results_count` | integer | * total number of results* |
| `item_types` | array | *types of search results*contains types of search results (`items`) found in SERP.possible item types:`gemini_text`, `gemini_table`, `gemini_images` |
| `items_count` | integer | *the number of results returned in the **`items`** array* |
| **`items`** | array | *elements of Gemini results* |
| **`gemini_text`** | object | *element in the response* |
| `type` | string | * type of element*=***'gemini_text'*** |
| `rank_group` | integer | *group rank in SERP*position within a group of elements with identical `type` valuespositions of elements with different `type` values are omitted from `rank_group` |
| `rank_absolute` | integer | *absolute rank in SERP*absolute position among all the elements in SERP |
| `markdown` | string | *content of the element in markdown format*content of the result formatted in the [markdown markup language](https://en.wikipedia.org/wiki/Markdown) |
| `original_text` | string | *unformatted text content of the element* |
| **`sources`** | array | *array of sources* |
| `type` | string | *type of element*=***'gemini_source'*** |
| `title` | string | *source title* |
| `snippet` | string | *source description* |
| `domain` | string | *source domain in SERP* |
| `url` | string | *source URL* |
| `thumbnail` | string | *source thumbnail* |
| `source_name` | string | *source name* |
| `publication_date` | string | *date and time when the result was published*in the format: “year-month-date:minutes:UTC_difference_hours:UTC_difference_minutes”example:`2019-11-15 12:57:46 +00:00` |
| `markdown` | string | *content of the element in markdown format*content of the result formatted in the [markdown markup language](https://en.wikipedia.org/wiki/Markdown) |
| **`gemini_table`** | object | *element in the response* |
| `type` | string | * type of element*=***'gemini_table'*** |
| `rank_group` | integer | *group rank in SERP*position within a group of elements with identical `type` valuespositions of elements with different `type` values are omitted from `rank_group` |
| `rank_absolute` | integer | *absolute rank in SERP*absolute position among all the elements in SERP |
| `markdown` | string | *content of the element in markdown format*content of the result formatted in the [markdown markup language](https://en.wikipedia.org/wiki/Markdown) |
| `original_text` | string | *unformatted text content of the element* |
| **`table`** | object | *table present in the element*the header and content of the table present in the element |
| `table_header` | array | *content in the header of the table* |
| `table_content` | array | *array of contents of the table present in the element*each array represents the table row |
| **`gemini_images`** | object | *element in the response* |
| `type` | string | * type of element*=***'gemini_images'*** |
| `rank_group` | integer | *group rank in SERP*position within a group of elements with identical `type` valuespositions of elements with different `type` values are omitted from `rank_group` |
| `rank_absolute` | integer | *absolute rank in SERP*absolute position among all the elements in SERP |
| `markdown` | string | *content of the element in markdown format*content of the result formatted in the [markdown markup language](https://en.wikipedia.org/wiki/Markdown) |
| **`items`** | array | *items present in the element* |
| `type` | string | *type of element = '**gemini_images_element**'* |
| `url` | string | *relevant URL* |
| `alt` | string | *alt tag of the image* |
| `image_url` | string | *URL of the image*the URL leading to the image on the original resource or DataForSEO storage (in case the original source is not available) |
| `markdown` | string | *content of the element in markdown format*content of the result formatted in the [markdown markup language](https://en.wikipedia.org/wiki/Markdown) |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


###### HTML
*Source: [https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/task_get/html/](https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/task_get/html/)*
#### Get Gemini LLM Scraper HTML

GEThttps://api.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/task_get/html/$id

Pricing

Your account will be charged only for posting a task. You can get the results of the task within the next 7 days for free.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/ai-optimization/llm-scraper) page.

**Description of the fields for sending a request:**

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

| Field name | Type | Description |
| --- | --- | --- |
| `id` | string | *task identifier***unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format**you will be able to use it within **7 days** to request the results of the task at any time |

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
| `status_code` | integer | *status code of the task*generated by DataForSEO; can be within the following range: 10000-60000you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `keyword` | string | *keyword received in a POST array***keyword is returned with decoded %## (plus symbol '+' will be decoded to a space character)** |
| `location_code` | integer | *location code in a POST array* |
| `language_code` | string | *language code in a POST array* |
| `datetime` | string | *date and time when the result was received*in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”example:`2019-11-15 12:57:46 +00:00` |
| `items_count` | integer | *the number of results returned in the **`items`** array* |
| **`items`** | array | *elements of search results found* |
| `page` | integer | *serial number of the returned HTML page* |
| `date` | string | *date and time when the HTML page was scanned*in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”example:`2019-11-15 12:57:46 +00:00` |
| `html` | string | *HTML page* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


###### Advanced
*Source: [https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/live/advanced/](https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/live/advanced/)*
#### Live Gemini LLM Scraper Advanced

Live Gemini LLM Scraper endpoint provides structured results from Gemini. The results are specific to the selected location (see [the List of Locations](https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/locations/)), language (see [the List of Languages](https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/languages/)), and keyword.

POSThttps://api.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/live/advanced

Pricing

The cost of the task can be calculated on the [Pricing page](https://dataforseo.com/pricing/ai-optimization/llm-scraper).

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute, each Live Gemini LLM Scraper API call can contain only one task.

**Execution time for tasks set with the Live Gemini LLM Scraper endpoint is currently up to 120 seconds.**

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `keyword` | string | *keyword***required field**you can specify **up to 2000 characters** in the `keyword` fieldall %## will be decoded (plus character ‘+’ will be decoded to a space character)if you need to use the “%” character for your `keyword`, please specify it as “%25”;if you need to use the “+” character for your `keyword`, please specify it as “%2B”learn more about rules and limitations of `keyword` and `keywords` fields in DataForSEO APIs in this [Help Center article](https://dataforseo.com/help-center/rules-and-limitations-of-keyword-and-keywords-fields-in-dataforseo-apis) |
| `location_name` | string | *full name of search engine location***required field if you don't specify** `location_code` or `location_coordinate`**if you use this field, you don't need to specify `location_code` or `location_coordinate`**you can receive the list of available locations of the search engine with their `location_name` by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/locations](https://api.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/locations)`example:`United States` |
| `location_code` | integer | *search engine location code***required field if you don't specify** `location_name` or `location_coordinate`**if you use this field, you don't need to specify `location_name` or `location_coordinate`**you can receive the list of available locations of the search engines with their `location_code` by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/locations](https://api.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/locations)`example:`2840` |
| `location_coordinate` | string | *GPS coordinates of a location***required field if you don't specify** `location_name` or `location_code`**if you use this field, you don't need to specify `location_name` or `location_code`**`location_coordinate` parameter should be specified in the *"latitude,longitude,radius"* formatthe maximum number of decimal digits for *"latitude"* and *"longitude"*: 7the minimum value for *"radius"*: 199 (mm)the maximum value for *"radius"*: 199999 (mm)example:`53.476225,-2.243572,200` |
| `language_name` | string | *full name of search engine language*required field if you don't specify `language_code`;if you use this field, you don't need to specify `language_code`;you can receive the list of available languages of the search engine with their `language_name` by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/languages](https://api.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/languages)`example: `English` |
| `language_code` | string | *search engine language code*required field if you don't specify `language_name`;if you use this field, you don't need to specify `language_name`;you can receive the list of available languages of the search engine with their `language_code`_by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/languages](https://api.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/languages)`example: `en`n |
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
| `status_code` | integer | *status code of the task*generated by DataForSEO; can be within the following range: 10000-60000you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `keyword` | string | *keyword received in a POST array***the keyword is returned with decoded %## (plus symbol '+' will be decoded to a space character)** |
| `location_code` | integer | *location code in a POST array* |
| `language_code` | string | *language code in a POST array* |
| `model` | string | *indicates the model version* |
| `datetime` | string | *date and time when the result was received*in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”example:`2019-11-15 12:57:46 +00:00` |
| `markdown` | string | *content of the element in markdown format*content of the result formatted in the [markdown markup language](https://en.wikipedia.org/wiki/Markdown) |
| **`sources`** | array | *array of sources*the sources the model actually cited or relied on in its final answer |
| `type` | string | *type of element*=***'gemini_source'*** |
| `title` | string | *source title* |
| `snippet` | string | *source description* |
| `domain` | string | *source domain* |
| `url` | string | *source URL* |
| `thumbnail` | string | *source thumbnail* |
| `source_name` | string | *source name* |
| `publication_date` | string | *date and time when the result was published*in the format: “year-month-date:minutes:UTC_difference_hours:UTC_difference_minutes”example:`2019-11-15 12:57:46 +00:00` |
| `markdown` | string | *content of the element in markdown format*content of the result formatted in the [markdown markup language](https://en.wikipedia.org/wiki/Markdown) |
| `se_results_count` | integer | * total number of results* |
| `item_types` | array | *types of search results*contains types of search results (`items`) found in SERP.possible item types:`gemini_text`, `gemini_table`, `gemini_images` |
| `items_count` | integer | *the number of results returned in the **`items`** array* |
| **`items`** | array | *elements of Gemini results* |
| **`gemini_text`** | object | *element in the response* |
| `type` | string | * type of element*=***'gemini_text'*** |
| `rank_group` | integer | *group rank in SERP*position within a group of elements with identical `type` valuespositions of elements with different `type` values are omitted from `rank_group` |
| `rank_absolute` | integer | *absolute rank in SERP*absolute position among all the elements in SERP |
| `markdown` | string | *content of the element in markdown format*content of the result formatted in the [markdown markup language](https://en.wikipedia.org/wiki/Markdown) |
| `original_text` | string | *unformatted text content of the element* |
| **`sources`** | array | *array of sources* |
| `type` | string | *type of element*=***'gemini_source'*** |
| `title` | string | *source title* |
| `snippet` | string | *source description* |
| `domain` | string | *source domain in SERP* |
| `url` | string | *source URL* |
| `thumbnail` | string | *source thumbnail* |
| `source_name` | string | *source name* |
| `publication_date` | string | *date and time when the result was published*in the format: “year-month-date:minutes:UTC_difference_hours:UTC_difference_minutes”example:`2019-11-15 12:57:46 +00:00` |
| `markdown` | string | *content of the element in markdown format*content of the result formatted in the [markdown markup language](https://en.wikipedia.org/wiki/Markdown) |
| **`gemini_table`** | object | *element in the response* |
| `type` | string | * type of element*=***'gemini_table'*** |
| `rank_group` | integer | *group rank in SERP*position within a group of elements with identical `type` valuespositions of elements with different `type` values are omitted from `rank_group` |
| `rank_absolute` | integer | *absolute rank in SERP*absolute position among all the elements in SERP |
| `markdown` | string | *content of the element in markdown format*content of the result formatted in the [markdown markup language](https://en.wikipedia.org/wiki/Markdown) |
| `original_text` | string | *unformatted text content of the element* |
| **`table`** | object | *table present in the element*the header and content of the table present in the element |
| `table_header` | array | *content in the header of the table* |
| `table_content` | array | *array of contents of the table present in the element*each array represents the table row |
| **`gemini_images`** | object | *element in the response* |
| `type` | string | * type of element*=***'gemini_images'*** |
| `rank_group` | integer | *group rank in SERP*position within a group of elements with identical `type` valuespositions of elements with different `type` values are omitted from `rank_group` |
| `rank_absolute` | integer | *absolute rank in SERP*absolute position among all the elements in SERP |
| `markdown` | string | *content of the element in markdown format*content of the result formatted in the [markdown markup language](https://en.wikipedia.org/wiki/Markdown) |
| **`items`** | array | *items present in the element* |
| `type` | string | *type of element = '**gemini_images_element**'* |
| `url` | string | *relevant URL* |
| `alt` | string | *alt tag of the image* |
| `image_url` | string | *URL of the image*the URL leading to the image on the original resource or DataForSEO storage (in case the original source is not available) |
| `markdown` | string | *content of the element in markdown format*content of the result formatted in the [markdown markup language](https://en.wikipedia.org/wiki/Markdown) |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


###### HTML
*Source: [https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/live/html/](https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/live/html/)*
#### Live Gemini LLM Scraper HTML

Live Gemini LLM Scraper API HTML provides a raw HTML page of the results for the specified keyword, language (see [the List of Languages](https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/languages/)), and location (see [the List of Locations](https://docs.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/locations/)).

POSThttps://api.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/live/html

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/ai-optimization/llm-scraper) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute, each Live LLM Scraper API call can contain only one task.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `keyword` | string | *keyword***required field**you can specify **up to 2000 characters** in the `keyword` fieldall %## will be decoded (plus character ‘+’ will be decoded to a space character)if you need to use the “%” character for your `keyword`, please specify it as “%25”;if you need to use the “+” character for your `keyword`, please specify it as “%2B”learn more about rules and limitations of `keyword` and `keywords` fields in DataForSEO APIs in this [Help Center article](https://dataforseo.com/help-center/rules-and-limitations-of-keyword-and-keywords-fields-in-dataforseo-apis) |
| `location_name` | string | *full name of search engine location***required field if you don't specify** `location_code` or `location_coordinate`**if you use this field, you don't need to specify `location_code` or `location_coordinate`**you can receive the list of available locations of the search engine with their `location_name` by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/locations](https://api.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/locations)`example:`United States` |
| `location_code` | integer | *search engine location code***required field if you don't specify** `location_name` or `location_coordinate`**if you use this field, you don't need to specify `location_name` or `location_coordinate`**you can receive the list of available locations of the search engines with their `location_code` by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/locations](https://api.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/locations)`example:`2840` |
| `location_coordinate` | string | *GPS coordinates of a location***required field if you don't specify** `location_name` or `location_code`**if you use this field, you don't need to specify `location_name` or `location_code`**`location_coordinate` parameter should be specified in the *"latitude,longitude,radius"* formatthe maximum number of decimal digits for *"latitude"* and *"longitude"*: 7the minimum value for *"radius"*: 199 (mm)the maximum value for *"radius"*: 199999 (mm)example:`53.476225,-2.243572,200` |
| `language_name` | string | *full name of search engine language***required field if you don't specify** `language_code`**if you use this field, you don't need to specify `language_code`**you can receive the list of available languages of the search engine with their `language_name` by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/languages](https://api.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/languages)`example:`English` |
| `language_code` | string | *search engine language code***required field if you don't specify** `language_name`**if you use this field, you don't need to specify `language_name`**you can receive the list of available languages of the search engine with their `language_code`_by making a separate request to the `[https://api.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/languages](https://api.dataforseo.com/v3/ai_optimization/gemini/llm_scraper/languages)`example:`en`n |
| `expand_citations` | boolean | *return expanded citation bar in HTML results*optional fieldwhen enabled, the endpoint will return HTML data from the expanded citation bar;default value: `false` |
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
| `status_code` | integer | *status code of the task*generated by DataForSEO; can be within the following range: 10000-60000you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the **`result`** array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `keyword` | string | *keyword received in a POST array***keyword is returned with decoded %## (plus character '+' will be decoded to a space character)** |
| `location_code` | integer | *location code in a POST array* |
| `language_code` | string | *language code in a POST array* |
| `datetime` | string | *date and time when the result was received*in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”example:`2019-11-15 12:57:46 +00:00` |
| `items_count` | integer | *the number of results returned in the **`items`** array* |
| **`items`** | array | *elements of search results found* |
| `page` | integer | *serial number of the returned HTML page* |
| `date` | string | *date and time when the HTML page was scanned*in the format: “year-month-date:minutes:UTC_difference_hours:UTC_difference_minutes”example:`2019-11-15 12:57:46 +00:00` |
| `html` | string | *HTML page* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Overview
*Source: [https://docs.dataforseo.com/v3/ai_optimization/perplexity/llm_responses/overview/](https://docs.dataforseo.com/v3/ai_optimization/perplexity/llm_responses/overview/)*
### Perplexity LLM Responses: Overview

This API allows you to generate and retrieve structured Perplexity responses

Perplexity LLM Responses API enables generation of structured responses from Perplexity, based on your specified input parameters. You can use this API to discover how Perplexity responds to queries about your brand, product, competitors, or any other target keywords and topics.

The endpoints of this API include:

• [Perplexity LLM Responses endpoint](https://docs.dataforseo.com/v3/ai_optimization/perplexity/llm_responses/live/) retrieves structured responses from a specific Perplexity AI model, based on your input parameters.

• [Perplexity LLM Responses Models endpoint](https://docs.dataforseo.com/v3/ai_optimization/perplexity/llm_responses/models/) provides a list of available Perplexity AI models you can use with Perplexity LLM Responses endpoint.

To find answers on common questions about AI Optimization API and find guidance on most efficient use, [visit our Help Center.](https://dataforseo.com/help-center/category/ai-optimization-api)

##### Methods

Perplexity LLM Responses API supports only the Live method of data retrieval. It doesn’t require making separate POST and GET requests to the corresponding endpoints and delivers instant results.

You can send up to 2000 API calls per minute. Contact us if you would like to raise the limit. Note that the maximum number of requests that can be sent simultaneously is limited to 30.

Execution time for tasks set with [Live Perplexity LLM Responses endpoint](https://docs.dataforseo.com/v3/ai_optimization/perplexity/llm_responses/live/) is currently **up to 120 seconds**.

##### Cost

The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/ai-optimization/llm-responses) page. You can check your spending in your [account dashboard](https://app.dataforseo.com/api-access) or by making a separate call to [the User Data endpoint](https://docs.dataforseo.com/v3/appendix/user_data/?php)

You can test Perplexity LLM Responses API for free using DataForSEO [Sandbox.](https://docs.dataforseo.com/v3/appendix/sandbox/)

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

---


##### Models
*Source: [https://docs.dataforseo.com/v3/ai_optimization/perplexity/llm_responses/models/](https://docs.dataforseo.com/v3/ai_optimization/perplexity/llm_responses/models/)*
#### Perplexity LLM Responses Models List

Pricing

Your account will not be charged for using this API

GEThttps://api.dataforseo.com/v3/ai_optimization/perplexity/llm_responses/models

You will receive the list of available Perplexity AI models by calling this API.
 
As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *general informational message*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total tasks cost, USD* |
| `tasks_count` | integer | *the number of tasks in the **`tasks`** array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier***unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*generated by DataForSEO; can be within the following range: 10000-60000you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the parameters passed in the URL of the GET request* |
| **`result`** | array | *array of results* |
| `model_name` | string | *name of the AI model* |
| `reasoning` | boolean | *indicates if the AI model supports reasoning* |
| `web_search_supported` | boolean | *web search support for the AI model*if `true`, the `web_search` parameter can be set with the AI model |
| `task_post_supported` | boolean | *indicates if Standard (POST-GET) data retrieval is supported*if `true`, you can use the [Standard (POST-GET)](https://dataforseo.com/help-center/live-vs-standard-method) data retrieval method with the AI model |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Live
*Source: [https://docs.dataforseo.com/v3/ai_optimization/perplexity/llm_responses/live/](https://docs.dataforseo.com/v3/ai_optimization/perplexity/llm_responses/live/)*
#### Live Perplexity LLM Responses

Live Perplexity LLM Responses endpoint allows you to retrieve structured responses from a specific Perplexity AI model, based on the input parameters.

**Note:** Perplexity uses `web_search` in all `sonar`-family models by default, but it’s not guaranteed to work with every request.

POSThttps://api.dataforseo.com/v3/ai_optimization/perplexity/llm_responses/live

Pricing

The cost of the task can be calculated on the [Pricing page](https://dataforseo.com/pricing/ai-optimization/llm-responses).

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute, each Live Perplexity LLM Responses call can contain only one task.

**The number of concurrent Live tasks is currently limited to 30 per account for each platform in the LLM Responses.**

**Execution time for tasks set with the Live Perplexity LLM Responses endpoint is currently up to 120 seconds.**

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `user_prompt` | string | *prompt for the AI model***required field**the question or task you want to send to the AI model;you can specify **up to 500 characters** in the `user_prompt` field |
| `model_name` | string | *name of the AI model***required field**`model_name`consists of the actual model name and version name;if the basic model name is specified, its latest version will be set by default;you can receive the list of available LLM models by making a separate request to the following endpoint: `[https://api.dataforseo.com/v3/ai_optimization/perplexity/llm_responses/models](https://api.dataforseo.com/v3/ai_optimization/perplexity/llm_responses/models)` |
| `max_output_tokens` | integer | *maximum number of tokens in the AI response*optional fieldminimum value: `1`maximum value: `4096`;default value: `2048`;**Note:** if the reasoning model is specified in the request, the output token count may exceed the specified `max_output_tokens` limit |
| `temperature` | float | *randomness of the AI response*optional fieldhigher values make output more diverse lower values make output more focusedminimum value: `0`maximum value: `1.9`default value: `0.77` |
| `top_p` | float | *diversity of the AI response*optional field controls diversity of the response by limiting token selectionminimum value: `0`maximum value: `1` default value: `0.9` |
| `web_search_country_iso_code` | string | *country code for web search localization*optional fieldspecify the country ISO code to get localized web search results**Note:** available only for Perplexity Sonar modelsexample: `US` |
| `system_message` | string | *instructions for the AI behavior*optional fielddefines the AI's role, tone, or specific behavior you can specify **up to 500 characters** in the `system_message` field |
| `message_chain` | array | *conversation history*optional fieldarray of message objects representing previous conversation turns;each object must contain:`role` string with either `user` or `ai` role;`message` string with message content (max 500 characters);you can specify **maximum of 10 message objects** in the array;**Note:** for Perplexity models, messages must strictly alternate between user and AI roles (`user` → `ai`);example:`"message_chain": [{"role":"user","message":"Hello, what’s up?"},{"role":"ai","message":"Hello! I’m doing well, thank you. How can I assist you today?"}]` |
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
| `status_code` | integer | *status code of the task*generated by DataForSEO; can be within the following range: 10000-60000you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD*includes the base task price plus the `money_spent` value |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `model_name` | string | *name of the AI model used* |
| `input_tokens` | integer | *number of tokens in the input*total count of tokens processed |
| `output_tokens` | integer | *number of tokens in the output*total count of tokens generated in the AI response |
| `web_search` | boolean | *indicates if web search was used***Note:** web search is enabled by default in Perplexity Sonar models |
| `money_spent` | float | *cost of AI tokens, USD*the price charged by the third-party AI model provider for according to its [Pricing](https://docs.perplexity.ai/guides/pricing) |
| `datetime` | string | *date and time when the result was received*in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”example:`2019-11-15 12:57:46 +00:00` |
| **`items`** | array | *array of response items*contains structured AI response data |
| `type` | string | *type of the element = **'message'*** |
| **`sections`** | array | *array of content sections*contains different parts of the AI response |
| `type` | string | *type of element*=***'text'*** |
| `text` | string | *AI-generated text content* |
| **`annotations`** | array | *array of references used to generate the response*equals `null` if the `web_search` parameter is not set to `true`**Note:** `annotations` may return empty even when `web_search` is `true`, as the AI will attempt to retrieve web information but may not find relevant results |
| `title` | string | *the domain name or title of the quoted source* |
| `url` | string | *URL of the quoted source* |
| `fan_out_queries` | array | *array of fan-out queries*contains related search queries derived from the main query to provide a more comprehensive response |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---
