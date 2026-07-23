# Keywords Data API Documentation
*Consolidated main text documentation of Keywords Data API compiled from docs.dataforseo.com*

---


### Overview
*Source: [https://docs.dataforseo.com/v3/keywords_data/overview/](https://docs.dataforseo.com/v3/keywords_data/overview/)*
### Keywords Data API: Overview

This API is the ultimate source of data for keyword analysis

**Keywords Data API** encompasses two datasources (Google and Bing) working with a broad range of endpoints:

- **Google**
- [Search Volume](https://docs.dataforseo.com/v3/keywords_data/google_ads/search_volume/live/)
- [Keywords For Site](https://docs.dataforseo.com/v3/keywords_data/google_ads/keywords_for_site/live/)
- [Keywords For Keywords](https://docs.dataforseo.com/v3/keywords_data/google_ads/keywords_for_keywords/live/)
- [Ad Traffic By Keywords](https://docs.dataforseo.com/v3/keywords_data/google_ads/ad_traffic_by_keywords/live/)
- [Google Trends Explore](https://docs.dataforseo.com/v3/keywords_data/google_trends/explore/task_post/)

- **Bing**
- [Search Volume](https://docs.dataforseo.com/v3/keywords_data/bing/search_volume/live/)
- [Keywords For Site](https://docs.dataforseo.com/v3/keywords_data/bing/keywords_for_site/live/)
- [Keywords For Keywords](https://docs.dataforseo.com/v3/keywords_data/bing/keywords_for_keywords/live/)
- [Keyword Performance](https://docs.dataforseo.com/v3/keywords_data/bing/keyword_performance/live/)

###### Note that Google Ads Keywords Data API is based on the latest version of the [Google Ads API](https://developers.google.com/google-ads/api/docs/start) that has replaced legacy Google AdWords API. If you’re using [DataForSEO Google AdWords API](https://docs.dataforseo.com/v3/keywords_data/google/overview/?bash), you need to upgrade to [DataForSEO Google Ads API](https://docs.dataforseo.com/v3/keywords_data/google_ads/overview/?bash).

You can get the full list of available endpoints [here](https://docs.dataforseo.com/v3/keywords_data/endpoints/). The returned results are specific to the indicated language, location, and other endpoint-specific parameters.

The restrictions of Google and Bing endpoints of Keywords Data API are related to [Google Advertising Policy](https://support.google.com/adspolicy/answer/6014299?hl=en/) and [Microsoft Advertising Ad Policies and Guidelines](https://about.ads.microsoft.com/en-us/resources/policies) accordingly. Consequently, we are not able to return data for keywords that fall into such categories as weapons, tobacco, drugs, violence, terrorism, etc. If you want to learn more about Google restrictions and prohibited categories, [check the article on our blog.](https://dataforseo.com/google-restrictions-explained-why-you-do-not-get-any-search-volume-for-your-queries.html)

Please note that if you post, for instance, 100 keywords in a batch and at least one of them falls into one of the categories listed above, no data will be retrieved for the whole batch of keywords.

To find answers on common questions about Keywords Data API and find guidance on efficient use of its features, [visit our Help Center.](https://dataforseo.com/help-center/category/keyword-data-api)

##### Methods

The cost of using Keywords Data endpoints depends on the selected method and priority of task execution. Available methods and priorities are described below.

DataForSEO has two main methods to deliver the results: Standard and Live.

If your system requires delivering instant results, **the Live method** is the best solution for you. Unlike the Standard method, this method doesn’t require making separate POST and GET requests to the corresponding endpoints.

If you don’t need to receive data in real-time, you can use **the Standard method** of data retrieval. This method requires making separate POST and GET requests, but it’s more affordable. Using this method, you can retrieve the results after our system collects them.

Alternatively, you can specify `pingback_url` or `postback_url` when setting a task, and we will notify you on completion of tasks or send them to you respectively.

If you need to set several tasks, you can receive the list of `id` for all completed tasks using **‘Tasks Ready’ endpoint,** and then collect the results of each separate task using ‘Task GET’ endpoint.

You can send up to 2000 API calls per minute. Contact us if you would like to raise the limit.

Visit [DataForSEO Help Center](https://dataforseo.com/help-center/best-practices-for-handling-keywords-data-api-requests) to get practical tips for request handling depending on your Keyword Data API payload volume.

##### Cost

The price depends on the method of data retrieval. The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data) page. You can check your spending in your [account dashboard](https://app.dataforseo.com/api-access) or by making a separate call to [the User Data endpoint](https://docs.dataforseo.com/v3/appendix/user_data/?php)

You can test Keywords Data API for free using DataForSEO [Sandbox.](https://docs.dataforseo.com/v3/appendix/sandbox/)

---


#### Overview
*Source: [https://docs.dataforseo.com/v3/keywords_data/google_ads/overview/](https://docs.dataforseo.com/v3/keywords_data/google_ads/overview/)*
### Google Ads Keywords Data API: Overview

This API is the ultimate source of data for keyword analysis

Using **Google Ads Keywords Data API** you can:

- Get [Search Volume](https://docs.dataforseo.com/v3/keywords_data/google_ads/search_volume/live/) and other metrics for up to 1000 keywords
- Indicate a domain and obtain up to 2000 [Keywords For Site](https://docs.dataforseo.com/v3/keywords_data/google_ads/keywords_for_site/live/)
- Specify up to 20 terms and get up to 20,000 [Keywords For Keywords](https://docs.dataforseo.com/v3/keywords_data/google_ads/keywords_for_keywords/live/)
- Get impressions, CPC, and clicks for up to 1000 terms with [Ad Traffic By Keywords](https://docs.dataforseo.com/v3/keywords_data/google_ads/ad_traffic_by_keywords/live/)

You can get the full list of available endpoints [here](https://docs.dataforseo.com/v3/keywords_data/endpoints/). The returned results are specific to the parameters indicated in the POST request. We use [Google Ads API](https://developers.google.com/google-ads/api/docs/start) as a data source. Thus, the locations supported in Google Ads Keyword Data API are identical to [Google Geographical Targeting.](https://developers.google.com/google-ads/api/reference/data/geotargets)

Subsequently the restrictions of Keywords Data API are related to [Google Advertising Policy](https://support.google.com/adspolicy/answer/6014299?hl=en/). We are not able to return data for keywords that fall into such categories as weapons, tobacco, drugs, violence, terrorism, etc. If you want to learn more about Google restrictions and prohibited categories, [check the article on our blog.](https://dataforseo.com/google-restrictions-explained-why-you-do-not-get-any-search-volume-for-your-queries.html)

Generally, Google updates keyword data in the middle of the month. Use the [Google Ads Status](https://docs.dataforseo.com/v3/keywords_data/google_ads/status/) endpoint to check if Google updated keyword data for the previous month.

##### Methods

The cost of using Keywords Data endpoints depends on the selected method of task execution. Available methods are described below.

DataForSEO has two main methods to deliver the results: Standard and Live.

If your system requires delivering instant results, **the Live method** is the best solution for you. Unlike the Standard method, this method doesn’t require making separate POST and GET requests to the corresponding endpoints.

###### Note: you can send no more than 12 requests per minute per account using Google Ads Live endpoints.

If you don’t need to receive data in real-time, you can use **the Standard method** of data retrieval. This method requires making separate POST and GET requests, but it’s more affordable. Using this method, you can retrieve the results after our system collects them.

Alternatively, you can specify `pingback_url` or `postback_url` when setting a task, and we will notify you on completion of tasks or send them to you respectively.

If you need to set several tasks, you can receive the list of `id` for all completed tasks using **‘Tasks Ready’ endpoint**, and then collect the results of each separate task using ‘Task GET’ endpoint.

Learn more about task completion and obtaining a list of completed tasks in [this help center article.](https://dataforseo.com/help-center/completed-tasks)

You can send up to 2000 API calls per minute. Contact us if you would like to raise the limit.

Visit [DataForSEO Help Center](https://dataforseo.com/help-center/best-practices-for-handling-keywords-data-api-requests) to get practical tips for request handling depending on your Keyword Data API payload volume.

##### Cost

The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/google-ads) page. You can check your spending in your [account dashboard](https://app.dataforseo.com/api-access) or by making a separate call to [the User Data endpoint](https://docs.dataforseo.com/v3/appendix/user_data/?php)

You can test Google Ads Keywords Data API for free using DataForSEO [Sandbox.](https://docs.dataforseo.com/v3/appendix/sandbox/)

---


#### Google Ads Status
*Source: [https://docs.dataforseo.com/v3/keywords_data/google_ads/status/](https://docs.dataforseo.com/v3/keywords_data/google_ads/status/)*
#### Google Ads Status

By calling this endpoint, you will know if Google updated keyword data for the previous month. Generally, Google updates keyword data in the middle of the month. So, if Google updated its data in October, you would be able to see the actual search volume, cost-per-click, competition, and other metrics for September. If Google didn’t update its data in October, the latest information would be available for August.

Pricing

Your account will not be charged for using this API

GEThttps://api.dataforseo.com/v3/keywords_data/google_ads/status

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

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
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *the data specified in the API call* |
| **`result`** | array | *array of results* |
| `actual_data` | boolean | *indicates whether Google updated keyword data for the previous month*<br>generally, Google updates keyword data in the middle of the month<br>if the value is `true`, Google currently provides up-to-date data for the previous month<br>if the value is `false`, we are not able to provide data for the previous month |
| `date_update` | string | *date of the latest update of Google Ads data*<br>indicates the latest date when Google updated search volume, CPC, and other keyword metrics<br>example:<br>`2020-05-15` |
| `last_year_in_monthly_searches` | integer | *the latest year for which search volume data is available*<br> |
| `last_month_in_monthly_searches` | integer | *the latest month for which search volume data is available*<br> |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


#### Locations
*Source: [https://docs.dataforseo.com/v3/keywords_data/google_ads/locations/](https://docs.dataforseo.com/v3/keywords_data/google_ads/locations/)*
#### List of ‘Google Ads’ Locations for Keywords Data

We use Google Geographical Targeting. You can refer to [Google Ads Target Types](https://developers.google.com/google-ads/api/reference/data/geotargets) page to review the full list of possible location types. With Keywords Data API, you can select any location type supported by Google, except for “Okrug”.
Postal Codes can be used to set a task, albeit API response will not return data for such tasks.

##### **Note:** All locations in Russia and Belarus are no longer supported across all DataForSEO services due to the invasion of Ukraine.

GEThttps://api.dataforseo.com/v3/keywords_data/google_ads/locations

GEThttps://api.dataforseo.com/v3/keywords_data/google_ads/locations/$country

Pricing

Your account will not be charged for using this API

You will receive the list of locations by this API call. You can filter the list of locations by country when setting a task.

You can also [download the full list of supported locations](https://cdn.dataforseo.com/v3/locations/locations_kwrd_2026_06_10.csv) in the CSV format (last updated 2026-06-10).

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information about available locations.

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
| `location_code_parent` | integer | *the code of the superordinate location*<br>example:<br>`"location_code": 9041134,<br>"location_name": "Vienna International Airport,Lower Austria,Austria",<br>"location_code_parent": 20044`<br>where `location_code_parent` corresponds to:<br>`"location_code": 20044,<br>"location_name": "Lower Austria,Austria"` |
| `country_iso_code` | string | *ISO country code of the location* |
| `location_type` | string | *location type*<br>possible values according to [Google’s target types](https://developers.google.com/adwords/api/docs/appendix/geotargeting) |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


#### Languages
*Source: [https://docs.dataforseo.com/v3/keywords_data/google_ads/languages/](https://docs.dataforseo.com/v3/keywords_data/google_ads/languages/)*
#### List of ‘Google Ads’ Languages for Keywords Data

Pricing

Your account will not be charged for using this API

GEThttps://api.dataforseo.com/v3/keywords_data/google_ads/languages

By calling this API you will receive the list of languages supported by Keywords Data API.

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information about available languages.

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
| `language_name` | string | *language name* |
| `language_code` | string | *language code according to [ISO 639-1](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes)* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Task POST
*Source: [https://docs.dataforseo.com/v3/keywords_data/google_ads/search_volume/task_post/](https://docs.dataforseo.com/v3/keywords_data/google_ads/search_volume/task_post/)*
#### Setting ‘Search Volume’ Tasks

Note that Google Ads Keywords Data API is based on the latest version of the [Google Ads API](https://developers.google.com/google-ads/api/docs/start) that has replaced legacy Google AdWords API. If you’re using [DataForSEO Google AdWords API](https://docs.dataforseo.com/v3/keywords_data/google/overview/?bash), you need to upgrade to [DataForSEO Google Ads API](https://docs.dataforseo.com/v3/keywords_data/google_ads/overview/?bash).

This endpoint will provide you with search volume, monthly searches, competition, and other related data for up to 1000 keywords in a single request.

This is the Standard method of data retrieval. If you don’t need to receive data in real-time, this method is the best option for you. Set a task and retrieve the results when our system collects them. Execution time depends on the system workload.

If your system requires delivering instant results, [the Live method](https://docs.dataforseo.com/v3/keywords_data/google_ads/search_volume/live/) will be a better solution. This method doesn’t require making separate POST and GET requests to the corresponding endpoints.

Historical data is available for 4 years.

POSThttps://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/task_post

Pricing

Your account will be charged only for setting a task.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/google-ads) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). Task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute, with each POST call containing no more than 100 tasks. If your POST call contains over 100 tasks, the tasks over this limit will return the `40006` error. Visit [DataForSEO Help Center](https://dataforseo.com/help-center/best-practices-for-handling-keywords-data-api-requests) to get practical tips for request handling depending on your Keyword Data API payload volume.

You will get information for every single keyword in an array.

You can send up to 1000 keywords in one `keywords` array. Our system will charge your account per each request, no matter what number of keywords an array has, the price for 1 or 1000 keywords will be the same.

You can also retrieve the results of completed tasks using the unique task identifier `id`. Alternatively, we can send them to you as soon as they are ready if you specify the `postback_url` or `pingback_url` when setting a task. Note that if your server doesn’t respond within 10 seconds, the connection will be aborted by timeout, and the task will be transferred to the [tasks_ready](https://docs.dataforseo.com/v3/keywords_data/google_ads/search_volume/tasks_ready/?php) list. The error code and message depend on your server’s configuration.

See [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) to learn more about using pingbacks and postbacks with DataForSEO APIs.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

optional field

| Field name | Type | Description |
| --- | --- | --- |
| `keywords` | array | *keywords*<br>**required field**<br>The maximum number of keywords you can specify: 1000<br>The maximum number of characters for each keyword: 80<br>The maximum number of words for each keyword phrase: 10<br>the keywords you specify will be converted to a lowercase format<br>**Note #1:** [Google Ads may return no data for certain groups of keywords](https://dataforseo.com/help-center/no-search-volume-data-for-some-keywords);<br>**Note #2:** [Google Ads provides combined search volume values for groups of similar keywords](https://dataforseo.com/help-center/sv-broad-exact-phrase-match)<br>to obtain search volume for similar keywords, we recommend submitting such keywords in separate requests;<br>**Note #3:** Google Ads doesn’t allow using certain symbols and characters (e.g., UTF symbols, emojis), so you can’t use them when setting a task;<br>to learn more about which symbols and characters can be used, please refer to [this article](https://dataforseo.com/help-center/using-symbols-in-keywords-when-setting-a-google-ads-task)<br>learn more about rules and limitations of `keyword` and `keywords` fields in DataForSEO APIs in this [Help Center article](https://dataforseo.com/help-center/rules-and-limitations-of-keyword-and-keywords-fields-in-dataforseo-apis) |
| `location_name` | string | *full name of search engine location*<br>optional field<br>if you do not indicate the location, you will receive worldwide results, i.e., for all available locations;<br>**if you use this field, you don’t need to specify `location_code` or `location_coordinate`**<br>you can receive the list of available locations of the search engine with their `location_name` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/google_ads/locations`<br>example:<br>`London,England,United Kingdom` |
| `location_code` | integer | *search engine location code*<br>optional field<br>if you do not indicate the location, you will receive worldwide results, i.e., for all available locations;<br>**if you use this field, you don’t need to specify `location_name` or `location_coordinate`**;<br>you can receive the list of available locations of the search engines with their `location_code` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/google_ads/locations`<br>example:<br>`2840` |
| `location_coordinate` | string | *GPS coordinates of a location*<br>optional field<br>if you do not indicate the location, you will receive worldwide results, i.e., for all available locations;<br>**if you use this field, you don’t need to specify `location_name` or `location_code`**;<br>`location_coordinate` parameter should be specified in the *“latitude,longitude”* format;<br>**the data will be provided for the country the specified coordinates belong to**;<br>example:<br>`52.6178549,-155.352142` |
| `language_name` | string | *full name of search engine language*<br>optional field<br>you can receive the list of available languages of the search engine with their `language_name` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/google_ads/languages`<br>example:<br>`English` |
| `language_code` | string | *search engine language code*<br>optional field<br>you can receive the list of available languages of the search engine with their `language_code` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/google_ads/languages`<br>example:<br>`en` |
| `search_partners` | boolean | *include Google search partners*<br>optional field<br>if you specify `true`, the results will be delivered for owned, operated, and syndicated networks across [Google and partner sites](https://support.google.com/google-ads/answer/1722047?hl=en) that host Google search;<br>default value: `false` – results are returned for Google search sites |
| `date_from` | string | *starting date of the time range*<br>optional field<br>date format: `"yyyy-mm-dd"`<br>minimal value: 4 years from the current date<br>by default, data is returned for the past 12 months;<br>**Note**: the indicated date cannot be greater than that specified in `date_to` and/or yesterday’s date;if [Status endpoint](https://docs.dataforseo.com/v3/keywords_data/google_ads/status/) returns `false` in the `actual_data` field, `date_from` can be set to the month before last and prior;<br>if [Status endpoint](https://docs.dataforseo.com/v3/keywords_data/google_ads/status/) returns `true` in the `actual_data` field, `date_from` can be set to the last month and prior |
| `date_to` | string | *ending date of the time range*<br>optional field<br>**Note:** the indicated date cannot be greater than the past month, Google Ads does not return data on the current month;<br>if you don’t specify this field, yesterday’s date will be used by default<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2022-11-30"` |
| `include_adult_keywords` | boolean | *include keywords associated with adult content<br>*optional field*<br>*if set to `true`, adult keywords will be included in the response<br>default value: `false`<br>**note** that the API may return no data for such keywords due to [Google Ads restrictions](https://support.google.com/adspolicy/answer/6008942?hl=en) |
| `sort_by` | string | *results sorting parameters*<br>optional field<br>use these parameters to sort the results by `relevance`, `search_volume`, `competition_index`, `low_top_of_page_bid`, or `high_top_of_page_bid` in the descending order<br>default value: `relevance` |
| `postback_url` | string | *URL for sending task results*<br>optional field<br>once the task is completed, we will send a POST request with its results compressed in the `gzip` format to the `postback_url` you specified<br>you can use the ‘$id’ string as a `$id` variable and ‘$tag’ as urlencoded `$tag` variable. We will set the necessary values before sending the request.<br>example:<br>`http://your-server.com/postbackscript?id=$id`<br>`http://your-server.com/postbackscript?id=$id&tag=$tag`<br>**Note:** special character in `postback_url` will be urlencoded;<br>i.a., the `#` character will be encoded into `%23`<br>learn more on our [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) |
| `pingback_url` | string | *notification URL of a completed task*<br>optional field<br>when a task is completed we will notify you by GET request sent to the URL you have specified<br>you can use the ‘$id’ string as a `$id` variable and ‘$tag’ as urlencoded `$tag` variable. We will set the necessary values before sending the request<br>example:<br>`http://your-server.com/pingscript?id=$id`<br>`http://your-server.com/pingscript?id=$id&tag=$tag`<br>**Note:** special character in `pingback_url` will be urlencoded;<br>i.a., the `#` character will be encoded into `%23`<br>learn more on our [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) |
| `tag` | string | *user-defined task identifier*<br>optional field<br>*the character limit is 255*<br>you can use this parameter to identify the task and match it with the result<br>you will find the specified `tag` value in the `data` array of the response |

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
*Source: [https://docs.dataforseo.com/v3/keywords_data/google_ads/search_volume/tasks_ready/](https://docs.dataforseo.com/v3/keywords_data/google_ads/search_volume/tasks_ready/)*
#### Get ‘Search Volume’ Completed Tasks

This endpoint is designed to provide you with a list of completed tasks, which haven’t been collected yet. If you use the Standard method without specifying the `postback_url`, you can receive the list of `id` for all completed tasks using this endpoint. Then, you can collect the results using the **‘Task GET’** endpoint.

Learn more about task completion and obtaining a list of completed tasks in [this help center article.](https://dataforseo.com/help-center/completed-tasks)

**Note:** due to the peculiarities of our architecture the queue of completed tasks is updated with a small delay, which can be an issue for high-volume users. If your system requires collecting over 1000 tasks a minute, we recommend using [pingbacks/postbacks](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) instead, and applying the Tasks Ready endpoint only to obtain the IDs of failed postback tasks.

GEThttps://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/tasks_ready

Pricing

Your account will not be charged when receiving results

Each separate task will remain on the list until it is collected. You can make **up to 20 API calls per minute.** With each API call, you can get 1000 tasks completed within three previous days. The list will not contain the tasks which have already been collected and the tasks that were not collected **within the three days** after completion.

Please note that if you specify the `postback_url`, the task will not be in the list of completed tasks. The task can only be found in the list if the request to your server failed, and your server returned HTTP code response less than `200` or higher than `300`.

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
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the parameters passed in the request’s URL* |
| ** `result`** | array | *array of results* |
| `id` | string | *task identifier of the completed task*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `se` | string | *search engine specified when setting the task* |
| `function` | string | *type of the task* |
| `date_posted` | string | *date when the task was posted (in the UTC format)* |
| `endpoint` | string | *URL for collecting the results of the task* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Task GET
*Source: [https://docs.dataforseo.com/v3/keywords_data/google_ads/search_volume/task_get/](https://docs.dataforseo.com/v3/keywords_data/google_ads/search_volume/task_get/)*
#### Get Search Volume Results by id

Note that Google Ads Keywords Data API is based on the latest version of the [Google Ads API](https://developers.google.com/google-ads/api/docs/start) that has replaced legacy Google AdWords API. If you’re using [DataForSEO Google AdWords API](https://docs.dataforseo.com/v3/keywords_data/google/overview/?bash), you need to upgrade to [DataForSEO Google Ads API](https://docs.dataforseo.com/v3/keywords_data/google_ads/overview/?bash).

This endpoint will provide you with search volume, monthly searches, competition, and other related data for up to 1000 keywords in a single request.

GEThttps://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/task_get/$id

Pricing

Your account will be charged only for posting a task. You can get the results of the task within the next 30 days for free.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/google-ads) page.

**Description of the fields for sending a request:**

| Field name | Type | Description |
| --- | --- | --- |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format**<br>you will be able to use it within **30 days** to request the results of the task at any time |

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
| `status_code` | integer | *status code of the task *<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | array | *contains the same parameters that you specified in the POST request<br>* |
| **`result`** | array | *array of results* |
| `keyword` | string | *keyword<br>***keyword is returned with decoded %## (plus character ‘+’ will be decoded to a space character)** |
| `spell` | string | *correct spelling of the keyword*<br>**Note:**if the keyword in the POST array appears to be misspelled, data will be returned for the correctly spelled keyword;<br>we use the functionality of Google Ads API to check and validate the spelling of keywords, [learn more by this link](https://support.google.com/google-ads/answer/7476658) |
| `location_code` | integer | *location code in a POST array*<br>if there is no data, then the value is `null` |
| `language_code` | string | *language code in a POST array*<br>if there is no data, then the value is `null` |
| `search_partners` | boolean | *indicates whether data from partner networks included in the response* |
| `competition` | string | *competition*<br>represents the relative amount of competition associated with the given keyword in paid SERP only;<br>this value is based on Google Ads data and can take the following values: `HIGH`, `MEDIUM`, `LOW`;<br>if there is no data the value is `null`;<br>learn more about the metric in [this help center article](https://dataforseo.com/help-center/what-is-competition) |
| `competition_index` | integer | *competition*<br>represents the relative amount of competition associated with the given keyword in paid SERP only;<br>this value is based on Google Ads data and can be between 0 and 100 (inclusive);<br>if there is no data the value is `null`;<br>learn more about the metric in [this help center article](https://dataforseo.com/help-center/what-is-competition) |
| `search_volume` | integer | *monthly average search volume rate;<br>*represents either the (approximate) number of searches for the given keyword idea on google.com or google.com and partners, depending on the user’s targeting;<br>if there is no data then the value is `null` |
| `low_top_of_page_bid` | float | *minimum bid for the ad to be displayed at the top of the first page*<br>indicates the value greater than about 20% of the lowest bids for which ads were displayed (based on Google Ads statistics for advertisers);<br>the value may differ depending on the location specified in a POST request |
| `high_top_of_page_bid` | float | *maximum bid for the ad to be displayed at the top of the first page*<br>indicates the value greater than about 80% of the lowest bids for which ads were displayed (based on Google Ads statistics for advertisers);<br>the value may differ depending on the location specified in a POST request |
| `cpc` | float | *cost per click*<br>indicates the amount paid (USD) for each click on the ad displayed for a given keyword<br> |
| `monthly_searches` | array | *monthly searches*<br>represents the (approximate) number of searches on this keyword idea (as available for the past twelve months by default), targeted to the specified geographic locations;<br>if there is no data then the value is `null` |
| `year` | integer | *year* |
| `month` | integer | *month* |
| `search_volume` | integer | *monthly average search volume rate* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Live
*Source: [https://docs.dataforseo.com/v3/keywords_data/google_ads/search_volume/live/](https://docs.dataforseo.com/v3/keywords_data/google_ads/search_volume/live/)*
#### Setting Live ‘Google Ads Search Volume’ Tasks

Note that Google Ads Keywords Data API is based on the latest version of the [Google Ads API](https://developers.google.com/google-ads/api/docs/start) that has replaced legacy Google AdWords API. If you’re using [DataForSEO Google AdWords API](https://docs.dataforseo.com/v3/keywords_data/google/overview/?bash), you need to upgrade to [DataForSEO Google Ads API](https://docs.dataforseo.com/v3/keywords_data/google_ads/overview/?bash).

This endpoint will provide you with search volume, monthly searches, competition, and other related data for up to 1000 keywords in a single request.
**Note: you can send no more than 12 requests per minute per account using Google Ads Live endpoints.**

Historical data is available for 4 years.

POSThttps://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/google-ads) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute. Visit [DataForSEO Help Center](https://dataforseo.com/help-center/best-practices-for-handling-keywords-data-api-requests) to get practical tips for request handling depending on your Keyword Data API payload volume.

You will get information for every single keyword in an array.

You can send up to 1000 keywords in one `keywords` array. Our system will charge your account per each request, no matter what number of keywords an array has, the price for 1 or 1000 keywords will be the same.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `keywords` | array | *keywords*<br>**required field**<br>The maximum number of keywords you can specify: 1000<br>The maximum number of characters for each keyword: 80<br>The maximum number of words for each keyword phrase: 10<br>the keywords you specify will be converted to a lowercase format<br>**Note #1:** [Google Ads may return no data for certain groups of keywords](https://dataforseo.com/help-center/no-search-volume-data-for-some-keywords);<br>**Note #2:** [Google Ads provides combined search volume values for groups of similar keywords](https://dataforseo.com/help-center/sv-broad-exact-phrase-match)<br>to obtain search volume for similar keywords, we recommend submitting such keywords in separate requests;<br>**Note #3:** Google Ads doesn’t allow using certain symbols and characters (e.g., UTF symbols, emojis), so you can’t use them when setting a task;<br>to learn more about which symbols and characters can be used, please refer to [this article](https://dataforseo.com/help-center/using-symbols-in-keywords-when-setting-a-google-ads-task)<br>learn more about rules and limitations of `keyword` and `keywords` fields in DataForSEO APIs in this [Help Center article](https://dataforseo.com/help-center/rules-and-limitations-of-keyword-and-keywords-fields-in-dataforseo-apis) |
| `location_name` | string | *full name of search engine location*<br>optional field<br>if you do not indicate the location, you will receive worldwide results, i.e., for all available locations;<br>**if you use this field, you don’t need to specify `location_code` or `location_coordinate`**<br>you can receive the list of available locations of the search engine with their `location_name` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/google_ads/locations`<br>example:<br>`London,England,United Kingdom` |
| `location_code` | integer | *search engine location code*<br>optional field<br>if you do not indicate the location, you will receive worldwide results, i.e., for all available locations;<br>**if you use this field, you don’t need to specify `location_name` or `location_coordinate`**;<br>you can receive the list of available locations of the search engines with their `location_code` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/google_ads/locations`<br>example:<br>`2840` |
| `location_coordinate` | string | *GPS coordinates of a location*<br>optional field<br>if you do not indicate the location, you will receive worldwide results, i.e., for all available locations;<br>**if you use this field, you don’t need to specify `location_name` or `location_code`**;<br>`location_coordinate` parameter should be specified in the *“latitude,longitude”* format;<br>**the data will be provided for the country the specified coordinates belong to**;<br>example:<br>`52.6178549,-155.352142` |
| `language_name` | string | *full name of search engine language*<br>optional field<br>you can receive the list of available languages of the search engine with their `language_name` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/google_ads/languages`<br>example:<br>`English` |
| `language_code` | string | *search engine language code*<br>optional field<br>you can receive the list of available languages of the search engine with their `language_code` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/google_ads/languages`<br>example:<br>`en` |
| `search_partners` | boolean | *include Google search partners*<br>optional field<br>if you specify `true`, the results will be delivered for owned, operated, and syndicated networks across [Google and partner sites](https://support.google.com/google-ads/answer/1722047?hl=en) that host Google search;<br>default value: `false` – results are returned for Google search sites |
| `date_from` | string | *starting date of the time range*<br>optional field<br>date format: `"yyyy-mm-dd"`<br>minimal value: 4 years from the current date<br>by default, data is returned for the past 12 months;<br>**Note**: the indicated date cannot be greater than that specified in `date_to` and/or yesterday’s date;if [Status endpoint](https://docs.dataforseo.com/v3/keywords_data/google_ads/status/) returns `false` in the `actual_data` field, `date_from` can be set to the month before last and prior;<br>if [Status endpoint](https://docs.dataforseo.com/v3/keywords_data/google_ads/status/) returns `true` in the `actual_data` field, `date_from` can be set to the last month and prior |
| `date_to` | string | *ending date of the time range*<br>optional field<br>**Note:** the indicated date cannot be greater than the past month, Google Ads does not return data on the current month;<br>if you don’t specify this field, yesterday’s date will be used by default<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2022-11-30"` |
| `include_adult_keywords` | boolean | *include keywords associated with adult content<br>*optional field<br>if set to `true`, adult keywords will be included in the response<br>default value: `false`<br>**note** that the API may return no data for such keywords due to [Google Ads restrictions](https://support.google.com/adspolicy/answer/6008942?hl=en) |
| `sort_by` | string | *results sorting parameters*<br>optional field<br>use these parameters to sort the results by `relevance`, `search_volume`, `competition_index`, `low_top_of_page_bid`, or `high_top_of_page_bid` in the descending order<br>default value: `relevance` |
| `tag` | string | *user-defined task identifier*<br>optional field<br>*the character limit is 255*<br>you can use this parameter to identify the task and match it with the result<br>you will find the specified `tag` value in the `data` array of the response |

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
| `status_code` | integer | *status code of the task *<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | array | *contains the same parameters that you specified in the POST request<br>* |
| **`result`** | array | *array of results* |
| `keyword` | string | *keyword<br>***keyword is returned with decoded %## (plus character ‘+’ will be decoded to a space character)** |
| `spell` | string | *correct spelling of the keyword*<br>**Note:**if the keyword in the POST array appears to be misspelled, data will be returned for the correctly spelled keyword;<br>we use the functionality of Google Ads API to check and validate the spelling of keywords, [learn more by this link](https://support.google.com/google-ads/answer/7476658) |
| `location_code` | integer | *location code in a POST array*<br>if there is no data, then the value is `null` |
| `language_code` | string | *language code in a POST array*<br>if there is no data, then the value is `null` |
| `search_partners` | boolean | *indicates whether data from partner networks included in the response* |
| `competition` | string | *competition*<br>represents the relative amount of competition associated with the given keyword in paid SERP only;<br>this value is based on Google Ads data and can take the following values: `HIGH`, `MEDIUM`, `LOW`;<br>if there is no data the value is `null`;<br>learn more about the metric in [this help center article](https://dataforseo.com/help-center/what-is-competition) |
| `competition_index` | integer | *competition*<br>represents the relative amount of competition associated with the given keyword in paid SERP only;<br>this value is based on Google Ads data and can be between 0 and 100 (inclusive);<br>if there is no data the value is `null`;<br>learn more about the metric in [this help center article](https://dataforseo.com/help-center/what-is-competition) |
| `search_volume` | integer | *monthly average search volume rate;<br>*represents either the (approximate) number of searches for the given keyword idea on google.com or google.com and partners, depending on the user’s targeting;<br>if there is no data then the value is `null` |
| `low_top_of_page_bid` | float | *minimum bid for the ad to be displayed at the top of the first page*<br>indicates the value greater than about 20% of the lowest bids for which ads were displayed (based on Google Ads statistics for advertisers);<br>the value may differ depending on the location specified in a POST request |
| `high_top_of_page_bid` | float | *maximum bid for the ad to be displayed at the top of the first page*<br>indicates the value greater than about 80% of the lowest bids for which ads were displayed (based on Google Ads statistics for advertisers);<br>the value may differ depending on the location specified in a POST request |
| `cpc` | float | *cost per click*<br>indicates the amount paid (USD) for each click on the ad displayed for a given keyword<br> |
| `monthly_searches` | array | *monthly searches*<br>represents the (approximate) number of searches on this keyword idea (as available for the past twelve months by default), targeted to the specified geographic locations;<br>if there is no data then the value is `null` |
| `year` | integer | *year* |
| `month` | integer | *month* |
| `search_volume` | integer | *monthly average search volume rate* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Task POST
*Source: [https://docs.dataforseo.com/v3/keywords_data/google_ads/keywords_for_site/task_post/](https://docs.dataforseo.com/v3/keywords_data/google_ads/keywords_for_site/task_post/)*
#### Setting ‘Keywords For Site’ Tasks

Note that Google Ads Keywords Data API is based on the latest version of the [Google Ads API](https://developers.google.com/google-ads/api/docs/start) that has replaced legacy Google AdWords API. If you’re using [DataForSEO Google AdWords API](https://docs.dataforseo.com/v3/keywords_data/google/overview/?bash), you need to upgrade to [DataForSEO Google Ads API](https://docs.dataforseo.com/v3/keywords_data/google_ads/overview/?bash).

This endpoint will provide you with a list of keywords relevant to the specified domain along with their bids, search volumes for the last month, search volume trends for the last year (for estimating search volume dynamics), and competition levels.

This is the Standard method of data retrieval. If you don’t need to receive data in real-time, this method is the best option for you. Set a task and retrieve the results when our system collects them. Execution time depends on the system workload.

If your system requires delivering instant results, the [Live method](https://docs.dataforseo.com/v3/keywords_data/google_ads/keywords_for_site/live/?bash) will be a better solution. This method doesn’t require making separate POST and GET requests to the corresponding endpoints.

Historical data is available for 4 years.

POSThttps://api.dataforseo.com/v3/keywords_data/google_ads/keywords_for_site/task_post

Pricing

Your account will be charged only for setting a task.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/google-ads) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute, with each POST call containing no more than 100 tasks. If your POST call contains over 100 tasks, the tasks over this limit will return the `40006` error. Visit [DataForSEO Help Center](https://dataforseo.com/help-center/best-practices-for-handling-keywords-data-api-requests) to get practical tips for request handling depending on your Keyword Data API payload volume.

You can get up to 2000 keyword suggestions with all essential keyword data in response to one request. Your account will be charged for each request, no matter what number of keywords you receive in the result, the price for 1 or 2000 keywords will be the same.

You can also retrieve the results of completed tasks using the unique task identifier `id`. Alternatively, we can send them to you as soon as they are ready if you specify the `postback_url` or `pingback_url` when setting a task. Note that if your server doesn’t respond within 10 seconds, the connection will be aborted by timeout, and the task will be transferred to the [tasks_ready](https://docs.dataforseo.com/v3/keywords_data/google_ads/keywords_for_site/tasks_ready/?php) list. The error code and message depend on your server’s configuration.

See [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) to learn more about using pingbacks and postbacks with DataForSEO APIs.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

optional field

| Field name | Type | Description |
| --- | --- | --- |
| `target` | string | *domain or page*<br>**required field**<br>the domain name of the target website or the url of the target page;<br>**note:** to obtain keywords for the target website, use the `target_type` parameter |
| `target_type` | string | *search keywords for site or url*<br>optional field<br>possible values: `site`, `page`;<br>default value: `page`<br>if set to `site`, keywords will be provided for the entire site;<br>if set to `page`, keywords will be provided for the specified webpage |
| `location_name` | string | *full name of search engine location*<br>optional field<br>if you do not indicate the location, you will receive worldwide results, i.e., for all available locations;<br>**if you use this field, you don’t need to specify `location_code` or `location_coordinate`**<br>you can receive the list of available locations of the search engine with their `location_name` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/google_ads/locations`<br>example:<br>`London,England,United Kingdom` |
| `location_code` | integer | *search engine location code*<br>optional field<br>if you do not indicate the location, you will receive worldwide results, i.e., for all available locations;<br>**if you use this field, you don’t need to specify `location_name` or `location_coordinate`**;<br>you can receive the list of available locations of the search engines with their `location_code` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/google_ads/locations`<br>example:<br>`2840` |
| `location_coordinate` | string | *GPS coordinates of a location*<br>optional field<br>if you do not indicate the location, you will receive worldwide results, i.e., for all available locations;<br>**if you use this field, you don’t need to specify `location_name` or `location_code`**;<br>`location_coordinate` parameter should be specified in the *“latitude,longitude”* format;<br>**the data will be provided for the country the specified coordinates belong to**;<br>example:<br>`52.6178549,-155.352142` |
| `language_name` | string | *full name of search engine language*<br>optional field<br>you can receive the list of available languages of the search engine with their `language_name` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/google_ads/languages`<br>example:<br>`English` |
| `language_code` | string | *search engine language code*<br>optional field<br>you can receive the list of available languages of the search engine with their `language_code` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/google_ads/languages`<br>example:<br>`en` |
| `search_partners` | boolean | *include Google search partners*<br>optional field<br>if you specify `true`, the results will be delivered for owned, operated, and syndicated networks across [Google and partner sites](https://support.google.com/google-ads/answer/1722047?hl=en) that host Google search;<br>default value: `false` – results are returned for Google search sites |
| `date_from` | string | *starting date of the time range*<br>optional field<br>date format: `"yyyy-mm-dd"`<br>minimal value: 4 years from the current date<br>by default, data is returned for the past 12 months;<br>**Note**: the indicated date cannot be greater than that specified in `date_to` and/or yesterday’s date;if [Status endpoint](https://docs.dataforseo.com/v3/keywords_data/google_ads/status/) returns `false` in the `actual_data` field, `date_from` can be set to the month before last and prior;<br>if [Status endpoint](https://docs.dataforseo.com/v3/keywords_data/google_ads/status/) returns `true` in the `actual_data` field, `date_from` can be set to the last month and prior |
| `date_to` | string | *ending date of the time range*<br>optional field<br>**Note:** the indicated date cannot be greater than yesterday’s date;<br>if you don’t specify this field, yesterday’s date will be used by default<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2022-11-30"` |
| `include_adult_keywords` | boolean | *include keywords associated with adult content*<br>optional field<br>if set to `true`, adult keywords will be included in the response<br>default value: `false`<br>**note** that the API may return no data for such keywords due to [Google Ads restrictions](https://support.google.com/adspolicy/answer/6008942?hl=en) |
| `sort_by` | string | *results sorting parameters*<br>optional field<br>Use these parameters to sort the results by `relevance`, `search_volume`, `competition_index`, `low_top_of_page_bid`, or `high_top_of_page_bid` in descending order<br>default value: `relevance` |
| `postback_url` | string | *URL for sending task results*<br>optional field<br>once the task is completed, we will send a POST request with its results compressed in the `gzip` format to the `postback_url` you specified<br>you can use the ‘$id’ string as a `$id` variable and ‘$tag’ as urlencoded `$tag` variable. We will set the necessary values before sending the request.<br>example:<br>`http://your-server.com/postbackscript?id=$id`<br>`http://your-server.com/postbackscript?id=$id&tag=$tag`<br>**Note:** special characters in `postback_url` will be urlencoded;<br>i.a., the `#` character will be encoded into `%23`<br>learn more on our [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) |
| `pingback_url` | string | *notification URL of a completed task*<br>optional field<br>when a task is completed we will notify you by GET request sent to the URL you have specified<br>you can use the ‘$id’ string as a `$id` variable and ‘$tag’ as urlencoded `$tag` variable. We will set the necessary values before sending the request<br>example:<br>`http://your-server.com/pingscript?id=$id`<br>`http://your-server.com/pingscript?id=$id&tag=$tag`<br>**Note:** special characters in `pingback_url` will be urlencoded;<br>i.a., the `#` character will be encoded into `%23`<br>learn more on our [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) |
| `tag` | string | *user-defined task identifier*<br>optional field<br>*the character limit is 255*<br>you can use this parameter to identify the task and match it with the result<br>you will find the specified `tag` value in the `data` object of the response |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)<br>**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *general informational message* |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total *tasks* cost, USD* |
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
| `data` | object | *contains the same parameters that you specified in the POST request* |
| ** `result`** | array | *array of results*<br>in this case, the value will be `null` |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Tasks Ready
*Source: [https://docs.dataforseo.com/v3/keywords_data/google_ads/keywords_for_site/tasks_ready/](https://docs.dataforseo.com/v3/keywords_data/google_ads/keywords_for_site/tasks_ready/)*
#### Get ‘Keywords For Site’ Completed Tasks

This endpoint is designed to provide you with a list of completed tasks, which haven’t been collected yet. If you use the Standard method without specifying the `postback_url`, you can receive the list of `id` for all completed tasks using this endpoint. Then, you can collect the results using the **‘Task GET’** endpoint.

Learn more about task completion and obtaining a list of completed tasks in [this help center article.](https://dataforseo.com/help-center/completed-tasks)

**Note:** due to the peculiarities of our architecture the queue of completed tasks is updated with a small delay, which can be an issue for high-volume users. If your system requires collecting over 1000 tasks a minute, we recommend using [pingbacks/postbacks](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) instead, and applying the Tasks Ready endpoint only to obtain the IDs of failed postback tasks.

GEThttps://api.dataforseo.com/v3/keywords_data/google_ads/keywords_for_site/tasks_ready

Pricing

Your account will not be charged when receiving results

Each separate task will remain on the list until it is collected. You can make **up to 20 API calls per minute.** With each API call, you can get 1000 tasks completed within three previous days. The list will not contain the tasks which have already been collected and the tasks that were not collected **within the three days** after completion.

Please note that if you specify the `postback_url`, the task will not be in the list of completed tasks. The task can only be found in the list if the request to your server failed, and your server returned HTTP code response less than `200` or higher than `300`.

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
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the parameters passed in the request’s URL* |
| ** `result`** | array | *array of results* |
| `id` | string | *task identifier of the completed task*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `se` | string | *search engine specified when setting the task* |
| `function` | string | *type of the task* |
| `date_posted` | string | *date when the task was posted (in the UTC format)* |
| `endpoint` | string | *URL for collecting the results of the task* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Task GET
*Source: [https://docs.dataforseo.com/v3/keywords_data/google_ads/keywords_for_site/task_get/](https://docs.dataforseo.com/v3/keywords_data/google_ads/keywords_for_site/task_get/)*
#### Get ‘Keywords For Site’ Results by id

Note that Google Ads Keywords Data API is based on the latest version of the [Google Ads API](https://developers.google.com/google-ads/api/docs/start) that has replaced legacy Google AdWords API. If you’re using [DataForSEO Google AdWords API](https://docs.dataforseo.com/v3/keywords_data/google/overview/?bash), you need to upgrade to [DataForSEO Google Ads API](https://docs.dataforseo.com/v3/keywords_data/google_ads/overview/?bash).

This endpoint will provide you with a list of keywords relevant to the specified domain along with their bids, search volumes for the last month, search volume trends for the last year (for estimating search volume dynamics), and competition levels.

You can get up to 2000 keyword suggestions with all essential keyword data in response to one request. Your account will be charged for each request, no matter what number of keywords you receive in the result.

GEThttps://api.dataforseo.com/v3/keywords_data/google_ads/keywords_for_site/task_get/$id

Pricing

Your account will be charged only for posting a task. You can get the results of the task within the next 30 days for free.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/google-ads) page.

**Description of the fields for sending a request:**

| Field name | Type | Description |
| --- | --- | --- |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format**<br>you will be able to use it within **30 days** to request the results of the task at any time |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the result array:**

| `version` | string | *the current version of the API* |
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
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `keyword` | string | *keyword in a POST array* |
| `location_code` | integer | *location code in a POST array*<br>if there is no data, the value is `null` |
| `language_code` | string | *language code in a POST array*<br>if there is no data, the value is `null` |
| `search_partners` | boolean | *include Google search partners*<br>the value you specified when setting the task<br>if `true`, the results are returned for owned, operated, and syndicated networks across Google and partner sites that host Google search;<br>if `false`, the results are returned for Google search sites only |
| `competition` | string | *competition*<br>represents the relative level of competition associated with the given keyword in paid SERP only<br>possible values: `LOW`, `MEDIUM`, `HIGH`<br>if competition level is unknown, the value is `null`;<br>learn more about the metric in [this help center article](https://dataforseo.com/help-center/what-is-competition) |
| `competition_index` | integer | *competition index*<br>the competition index for the query indicating how competitive ad placement is for the keyword<br>can take values from 0 to 100<br>the level of competition from 0 to 100 is determined by the number of ad slots filled divided by the total number of ad slots available<br>if not enough data is available, the value is `null`;<br>learn more about the metric in [this help center article](https://dataforseo.com/help-center/what-is-competition) |
| `search_volume` | integer | *monthly average search volume rate*<br>represents the (approximate) number of searches for the given keyword idea either on google.com or google.com and partners, depending on the user’s targeting<br>if there is no data, the value is `null` |
| `low_top_of_page_bid` | float | *minimum bid for the ad to be displayed at the top of the first page*<br>indicates the value greater than about 20% of the lowest bids for which ads were displayed (based on Google Ads statistics for advertisers)<br>the value may differ depending on the location specified in a POST request |
| `high_top_of_page_bid` | float | *maximum bid for the ad to be displayed at the top of the first page*<br>indicates the value greater than about 80% of the lowest bids for which ads were displayed (based on Google Ads statistics for advertisers)<br>the value may differ depending on the location specified in a POST request |
| `cpc` | float | *cost per click*<br>indicates the amount paid (USD) for each click on the ad displayed for a given keyword |
| `monthly_searches` | array | *monthly searches*<br>represents the (approximate) number of searches on this keyword idea (as available for the past twelve months), targeted to the specified geographic locations<br>if there is no data, the value is `null` |
| `year` | integer | *year* |
| `month` | integer | *month* |
| `search_volume` | integer | *monthly average search volume rate* |
| `keyword_annotations` | object | *the annotations for the keyword* |
| `concepts` | array | *the list of concepts for the keyword* |
| `name` | string | *the concept name for the keyword in the concept_group* |
| `concept_group` | object | *the concept group of the concept details* |
| `name` | string | *the concept group name* |
| `type` | string | *the concept group type* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Live
*Source: [https://docs.dataforseo.com/v3/keywords_data/google_ads/keywords_for_site/live/](https://docs.dataforseo.com/v3/keywords_data/google_ads/keywords_for_site/live/)*
#### Setting Live ‘Keywords For Site’ Tasks

Note that Google Ads Keywords Data API is based on the latest version of the [Google Ads API](https://developers.google.com/google-ads/api/docs/start) that has replaced legacy Google AdWords API. If you’re using [DataForSEO Google AdWords API](https://docs.dataforseo.com/v3/keywords_data/google/overview/?bash), you need to upgrade to [DataForSEO Google Ads API](https://docs.dataforseo.com/v3/keywords_data/google_ads/overview/?bash).

This endpoint will provide you with a list of keywords relevant to the specified domain along with their bids, search volumes for the last month, search volume trends for the last year (for estimating search volume dynamics), and competition levels.

**Note: you can send no more than 12 requests per minute per account using Google Ads Live endpoints.**

Historical data is available for 4 years.

POSThttps://api.dataforseo.com/v3/keywords_data/google_ads/keywords_for_site/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/google-ads) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute. Visit [DataForSEO Help Center](https://dataforseo.com/help-center/best-practices-for-handling-keywords-data-api-requests) to get practical tips for request handling depending on your Keyword Data API payload volume.

You can get up to 2000 keyword suggestions with all essential keyword data in response to one request. Your account will be charged for each request, no matter what number of keywords you receive in the result.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `target` | string | *domain or page*<br>**required field**<br>the domain name of the target website or the url of the target page;<br>**note:** to obtain keywords for the target website, use the `target_type` parameter |
| `target_type` | string | *search keywords for site or for url*<br>optional field<br>possible values: `site`, `page`;<br>default value: `page`;<br>if set to `site`, keywords will be provided for the entire site;<br>if set to `page`, keywords will be provided for the specified webpage |
| `location_name` | string | *full name of search engine location*<br>optional field<br>if you do not indicate the location, you will receive worldwide results, i.e., for all available locations;<br>**if you use this field, you don’t need to specify `location_code` or `location_coordinate`**<br>you can receive the list of available locations of the search engine with their `location_name` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/google_ads/locations`<br>example:<br>`London,England,United Kingdom` |
| `location_code` | integer | *search engine location code*<br>optional field<br>if you do not indicate the location, you will receive worldwide results, i.e., for all available locations;<br>**if you use this field, you don’t need to specify `location_name` or `location_coordinate`**;<br>you can receive the list of available locations of the search engines with their `location_code` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/google_ads/locations`<br>example:<br>`2840` |
| `location_coordinate` | string | *GPS coordinates of a location*<br>optional field<br>if you do not indicate the location, you will receive worldwide results, i.e., for all available locations;<br>**if you use this field, you don’t need to specify `location_name` or `location_code`**;<br>`location_coordinate` parameter should be specified in the *“latitude,longitude”* format;<br>**the data will be provided for the country the specified coordinates belong to**;<br>example:<br>`52.6178549,-155.352142` |
| `language_name` | string | *full name of search engine language*<br>optional field<br>you can receive the list of available languages of the search engine with their `language_name` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/google_ads/languages`<br>example:<br>`English` |
| `language_code` | string | *search engine language code*<br>optional field<br>you can receive the list of available languages of the search engine with their `language_code` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/google_ads/languages`<br>example:<br>`en` |
| `search_partners` | boolean | *include Google search partners*<br>optional field<br>if you specify `true`, the results will be delivered for owned, operated, and syndicated networks across [Google and partner sites](https://support.google.com/google-ads/answer/1722047?hl=en) that host Google search;<br>default value: `false` – results are returned for Google search sites |
| `date_from` | string | *starting date of the time range*<br>optional field<br>date format: `"yyyy-mm-dd"`<br>minimal value: 4 years from the current date<br>by default, data is returned for the past 12 months;<br>**Note**: the indicated date cannot be greater than that specified in `date_to` and/or yesterday’s date;if [Status endpoint](https://docs.dataforseo.com/v3/keywords_data/google_ads/status/) returns `false` in the `actual_data` field, `date_from` can be set to the month before last and prior;<br>if [Status endpoint](https://docs.dataforseo.com/v3/keywords_data/google_ads/status/) returns `true` in the `actual_data` field, `date_from` can be set to the last month and prior |
| `date_to` | string | *ending date of the time range*<br>optional field<br>**Note:** the indicated date cannot be greater than yesterday’s date;<br>if you don’t specify this field, yesterday’s date will be used by default<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2022-11-30"` |
| `include_adult_keywords` | boolean | *include keywords associated with adult content*<br>optional field<br>if set to `true`, adult keywords will be included in the response<br>default value: `false`<br>**note** that the API may return no data for such keywords due to [Google Ads restrictions](https://support.google.com/adspolicy/answer/6008942?hl=en) |
| `sort_by` | string | *results sorting parameters*<br>optional field<br>Use these parameters to sort the results by `relevance`, `search_volume`, `competition_index`, `low_top_of_page_bid`, or `high_top_of_page_bid` in descending order<br>default value: `relevance` |
| `tag` | string | *user-defined task identifier*<br>optional field<br>*the character limit is 255*<br>you can use this parameter to identify the task and match it with the result<br>you will find the specified `tag` value in the `data` object of the response |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the result array:**

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
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `keyword` | string | *keyword in a POST array* |
| `location_code` | integer | *location code in a POST array*<br>if there is no data, the value is `null` |
| `language_code` | string | *language code in a POST array*<br>if there is no data, the value is `null` |
| `search_partners` | boolean | *include Google search partners*<br>the value you specified when setting the task<br>if `true`, the results are returned for owned, operated, and syndicated networks across Google and partner sites that host Google search;<br>if `false`, the results are returned for Google search sites only |
| `competition` | string | *competition*<br>represents the relative level of competition associated with the given keyword in paid SERP only<br>possible values: `LOW`, `MEDIUM`, `HIGH`<br>if competition level is unknown, the value is `null`;<br>learn more about the metric in [this help center article](https://dataforseo.com/help-center/what-is-competition) |
| `competition_index` | integer | *competition index*<br>the competition index for the query indicating how competitive ad placement is for the keyword<br>can take values from 0 to 100<br>the level of competition from 0 to 100 is determined by the number of ad slots filled divided by the total number of ad slots available<br>if not enough data is available, the value is `null`;<br>learn more about the metric in [this help center article](https://dataforseo.com/help-center/what-is-competition) |
| `search_volume` | integer | *monthly average search volume rate*<br>represents the (approximate) number of searches for the given keyword idea either on google.com or google.com and partners, depending on the user’s targeting<br>if there is no data, the value is `null` |
| `low_top_of_page_bid` | float | *minimum bid for the ad to be displayed at the top of the first page*<br>indicates the value greater than about 20% of the lowest bids for which ads were displayed (based on Google Ads statistics for advertisers)<br>the value may differ depending on the location specified in a POST request |
| `high_top_of_page_bid` | float | *maximum bid for the ad to be displayed at the top of the first page*<br>indicates the value greater than about 80% of the lowest bids for which ads were displayed (based on Google Ads statistics for advertisers)<br>the value may differ depending on the location specified in a POST request |
| `cpc` | float | *cost per click*<br>indicates the amount paid (USD) for each click on the ad displayed for a given keyword |
| `monthly_searches` | array | *monthly searches*<br>represents the (approximate) number of searches on this keyword idea (as available for the past twelve months), targeted to the specified geographic locations<br>if there is no data, the value is `null` |
| `year` | integer | *year* |
| `month` | integer | *month* |
| `search_volume` | integer | *monthly average search volume rate* |
| `keyword_annotations` | object | *the annotations for the keyword* |
| `concepts` | array | *the list of concepts for the keyword* |
| `name` | string | *the concept name for the keyword in the concept_group* |
| `concept_group` | object | *the concept group of the concept details* |
| `name` | string | *the concept group name* |
| `type` | string | *the concept group type* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Task POST
*Source: [https://docs.dataforseo.com/v3/keywords_data/google_ads/keywords_for_keywords/task_post/](https://docs.dataforseo.com/v3/keywords_data/google_ads/keywords_for_keywords/task_post/)*
#### Setting ‘Keywords For Keywords’ Tasks

Note that Google Ads Keywords Data API is based on the latest version of the [Google Ads API](https://developers.google.com/google-ads/api/docs/start) that has replaced legacy Google AdWords API. If you’re using [DataForSEO Google AdWords API](https://docs.dataforseo.com/v3/keywords_data/google/overview/?bash), you need to upgrade to [DataForSEO Google Ads API](https://docs.dataforseo.com/v3/keywords_data/google_ads/overview/?bash).

This endpoint will provide relevant keywords for the specified terms. Set up to 20 keywords in the `keywords` array and get keyword suggestions from Google Ads. You can get up to 20,000 keyword suggestions with all essential keyword data in response to one request.

This is the Standard method of data retrieval. If you don’t need to receive data in real-time, this method is the best option for you. Set a task and retrieve the results when our system collects them. Execution time depends on the system workload.

If your system requires delivering instant results, [the Live method](https://docs.dataforseo.com/v3/keywords_data/google_ads/keywords_for_keywords/live/) will be a better solution. This method doesn’t require making separate POST and GET requests to the corresponding endpoints.

Historical data is available for 4 years.

POSThttps://api.dataforseo.com/v3/keywords_data/google_ads/keywords_for_keywords/task_post

Pricing

Your account will be charged only for setting a task.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/google-ads) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute, with each POST call containing no more than 100 tasks. If your POST call contains over 100 tasks, the tasks over this limit will return the `40006` error. Visit [DataForSEO Help Center](https://dataforseo.com/help-center/best-practices-for-handling-keywords-data-api-requests) to get practical tips for request handling depending on your Keyword Data API payload volume.

You can also retrieve the results of completed tasks using the unique task identifier `id`. Alternatively, we can send them to you as soon as they are ready if you specify the `postback_url` or `pingback_url` when setting a task. Note that if your server doesn’t respond within 10 seconds, the connection will be aborted by timeout, and the task will be transferred to the [tasks_ready](https://docs.dataforseo.com/v3/keywords_data/google_ads/keywords_for_keywords/tasks_ready/?php) list. The error code and message depend on your server’s configuration.

See [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) to learn more about using pingbacks and postbacks with DataForSEO APIs.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `keywords` | array | *keywords*<br>**required field**<br>The maximum number of keywords you can specify: 20<br>The maximum number of characters for each keyword: 80<br>the keywords you specify will be converted to a lowercase format<br>**Note:** Google Ads may return no data for certain groups of keywords<br>[visit our Help Center to learn more](https://dataforseo.com/help-center/no-search-volume-data-for-some-keywords)<br>**Also note** that Google Ads doesn’t allow using certain symbols and characters (e.g., UTF symbols, emojis), so you can’t use them when setting a task;<br>to learn more about which symbols and characters can be used, please refer to [this article](https://dataforseo.com/help-center/using-symbols-in-keywords-when-setting-a-google-ads-task)<br>learn more about rules and limitations of `keyword` and `keywords` fields in DataForSEO APIs in this [Help Center article](https://dataforseo.com/help-center/rules-and-limitations-of-keyword-and-keywords-fields-in-dataforseo-apis) |
| `target` | string | *target website*<br>optional field<br>specify a website or URL to get a list of keywords relevant to it;<br>**Note:** if a website url is specified, you will still get keywords relevant for the entire website |
| `location_name` | string | *full name of search engine location*<br>optional field<br>if you do not indicate the location, you will receive worldwide results, i.e., for all available locations;<br>**if you use this field, you don’t need to specify `location_code` or `location_coordinate`**<br>you can receive the list of available locations of the search engine with their `location_name` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/google_ads/locations`<br>example:<br>`London,England,United Kingdom` |
| `location_code` | integer | *search engine location code*<br>optional field<br>if you do not indicate the location, you will receive worldwide results, i.e., for all available locations;<br>**if you use this field, you don’t need to specify `location_name` or `location_coordinate`**;<br>you can receive the list of available locations of the search engines with their `location_code` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/google_ads/locations`<br>example:<br>`2840` |
| `location_coordinate` | string | *GPS coordinates of a location*<br>optional field<br>if you do not indicate the location, you will receive worldwide results, i.e., for all available locations;<br>**if you use this field, you don’t need to specify `location_name` or `location_code`**;<br>`location_coordinate` parameter should be specified in the *“latitude,longitude”* format;<br>**the data will be provided for the country the specified coordinates belong to**;<br>example:<br>`52.6178549,-155.352142` |
| `language_name` | string | *full name of search engine language*<br>optional field<br>you can receive the list of available languages of the search engine with their `language_name` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/google_ads/languages`<br>example:<br>`English` |
| `language_code` | string | *search engine language code*<br>optional field<br>you can receive the list of available languages of the search engine with their `language_code` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/google_ads/languages`<br>example:<br>`en` |
| `search_partners` | boolean | *include Google search partners*<br>optional field<br>if you specify `true`, the results will be delivered for owned, operated, and syndicated networks across [Google and partner sites](https://support.google.com/google-ads/answer/1722047?hl=en) that host Google search;<br>default value: `false` – results are returned for Google search sites |
| `date_from` | string | *starting date of the time range*<br>optional field<br>date format: `"yyyy-mm-dd"`<br>minimal value: 4 years from the current date<br>by default, data is returned for the past 12 months;<br>**Note**: the indicated date cannot be greater than that specified in `date_to` and/or yesterday’s date;if [Status endpoint](https://docs.dataforseo.com/v3/keywords_data/google_ads/status/) returns `false` in the `actual_data` field, `date_from` can be set to the month before last and prior;<br>if [Status endpoint](https://docs.dataforseo.com/v3/keywords_data/google_ads/status/) returns `true` in the `actual_data` field, `date_from` can be set to the last month and prior |
| `date_to` | string | *ending date of the time range*<br>optional field<br>**Note:** the indicated date cannot be greater than yesterday’s date;<br>if you don’t specify this field, yesterday’s date will be used by default<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2022-11-30"` |
| `sort_by` | string | *results sorting parameters*<br>optional field<br>Use these parameters to sort the results by `relevance`, `search_volume`, `competition_index`, `low_top_of_page_bid`, or `high_top_of_page_bid` in descending order<br>default value: `relevance` |
| `include_adult_keywords` | boolean | *include keywords associated with adult content*<br>optional field<br>if set to `true`, adult keywords will be included in the response<br>default value: `false`<br>**note** that the API may return no data for such keywords due to [Google Ads restrictions](https://support.google.com/adspolicy/answer/6008942?hl=en) |
| `postback_url` | string | *URL for sending task results*<br>optional field<br>once the task is completed, we will send a POST request with its results compressed in the `gzip` format to the `postback_url` you specified<br>you can use the ‘$id’ string as a `$id` variable and ‘$tag’ as urlencoded `$tag` variable. We will set the necessary values before sending the request.<br>example:<br>`http://your-server.com/postbackscript?id=$id`<br>`http://your-server.com/postbackscript?id=$id&tag=$tag`<br>**Note:** special characters in `postback_url` will be urlencoded;<br>i.a., the `#` character will be encoded into `%23`<br>learn more on our [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) |
| `pingback_url` | string | *notification URL of a completed task*<br>optional field<br>when a task is completed we will notify you by GET request sent to the URL you have specified<br>you can use the ‘$id’ string as a `$id` variable and ‘$tag’ as urlencoded `$tag` variable. We will set the necessary values before sending the request<br>example:<br>`http://your-server.com/pingscript?id=$id`<br>`http://your-server.com/pingscript?id=$id&tag=$tag`<br>**Note:** special characters in `pingback_url` will be urlencoded;<br>i.a., the `#` character will be encoded into `%23`<br>learn more on our [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) |
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
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
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
*Source: [https://docs.dataforseo.com/v3/keywords_data/google_ads/keywords_for_keywords/tasks_ready/](https://docs.dataforseo.com/v3/keywords_data/google_ads/keywords_for_keywords/tasks_ready/)*
#### Get ‘Keywords For Keywords’ Completed Tasks

This endpoint is designed to provide you with a list of completed tasks, which haven’t been collected yet. If you use the Standard method without specifying the `postback_url`, you can receive the list of `id` for all completed tasks using this endpoint. Then, you can collect the results using the **‘Task GET’** endpoint.

Learn more about task completion and obtaining a list of completed tasks in [this help center article.](https://dataforseo.com/help-center/completed-tasks)

**Note:** due to the peculiarities of our architecture the queue of completed tasks is updated with a small delay, which can be an issue for high-volume users. If your system requires collecting over 1000 tasks a minute, we recommend using [pingbacks/postbacks](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) instead, and applying the Tasks Ready endpoint only to obtain the IDs of failed postback tasks.

GEThttps://api.dataforseo.com/v3/keywords_data/google_ads/keywords_for_keywords/tasks_ready

Pricing

Your account will not be charged when receiving results

Each separate task will remain on the list until it is collected. You can make **up to 20 API calls per minute.** With each API call, you can get 1000 tasks completed within three previous days. The list will not contain the tasks which have already been collected and the tasks that were not collected **within the three days** after completion.

Please note that if you specify the `postback_url`, the task will not be in the list of completed tasks. The task can only be found in the list if the request to your server failed, and your server returned HTTP code response less than `200` or higher than `300`.

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
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the parameters passed in the request’s URL* |
| ** `result`** | array | *array of results* |
| `id` | string | *task identifier of the completed task*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `se` | string | *search engine specified when setting the task* |
| `function` | string | *type of the task* |
| `date_posted` | string | *date when the task was posted (in the UTC format)* |
| `endpoint` | string | *URL for collecting the results of the task* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Task GET
*Source: [https://docs.dataforseo.com/v3/keywords_data/google_ads/keywords_for_keywords/task_get/](https://docs.dataforseo.com/v3/keywords_data/google_ads/keywords_for_keywords/task_get/)*
#### Get ‘Keywords For Keywords’ Results by id

Note that Google Ads Keywords Data API is based on the latest version of the [Google Ads API](https://developers.google.com/google-ads/api/docs/start) that has replaced legacy Google AdWords API. If you’re using [DataForSEO Google AdWords API](https://docs.dataforseo.com/v3/keywords_data/google/overview/?bash), you need to upgrade to [DataForSEO Google Ads API](https://docs.dataforseo.com/v3/keywords_data/google_ads/overview/?bash).

This endpoint will select relevant keywords for the specified terms. Set up to 20 keywords and get the results, which are suggested by Google Ads for your query.

GEThttps://api.dataforseo.com/v3/keywords_data/google_ads/keywords_for_keywords/task_get/$id

Pricing

Your account will be charged only for posting a task. You can get the results of the task within the next 30 days for free.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/google-ads) page.

**Description of the fields for sending a request:**

| Field name | Type | Description |
| --- | --- | --- |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format**<br>you will be able to use it within **30 days** to request the results of the task at any time |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the result array:**

| `version` | string | *the current version of the API* |
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
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `keyword` | string | *keyword in a POST array* |
| `location_code` | integer | *location code in a POST array*<br>if there is no data, the value is `null` |
| `language_code` | string | *language code in a POST array*<br>if there is no data, the value is `null` |
| `search_partners` | boolean | *include Google search partners*<br>the value you specified when setting the task<br>if `true`, the results are returned for owned, operated, and syndicated networks across Google and partner sites that host Google search;<br>if `false`, the results are returned for Google search sites only |
| `competition` | string | *competition*<br>represents the relative level of competition associated with the given keyword in paid SERP only<br>possible values: `LOW`, `MEDIUM`, `HIGH`<br>if competition level is unknown, the value is `null`;<br>learn more about the metric in [this help center article](https://dataforseo.com/help-center/what-is-competition) |
| `competition_index` | integer | *competition index*<br>the competition index for the query indicating how competitive ad placement is for the keyword<br>can take values from 0 to 100<br>the level of competition from 0 to 100 is determined by the number of ad slots filled divided by the total number of ad slots available<br>if not enough data is available, the value is `null`;<br>learn more about the metric in [this help center article](https://dataforseo.com/help-center/what-is-competition) |
| `search_volume` | integer | *monthly average search volume rate*<br>represents the (approximate) number of searches for the given keyword idea either on google.com or google.com and partners, depending on the user’s targeting<br>if there is no data, the value is `null` |
| `low_top_of_page_bid` | float | *minimum bid for the ad to be displayed at the top of the first page*<br>indicates the value greater than about 20% of the lowest bids for which ads were displayed (based on Google Ads statistics for advertisers)<br>the value may differ depending on the location specified in a POST request |
| `high_top_of_page_bid` | float | *maximum bid for the ad to be displayed at the top of the first page*<br>indicates the value greater than about 80% of the lowest bids for which ads were displayed (based on Google Ads statistics for advertisers)<br>the value may differ depending on the location specified in a POST request |
| `cpc` | float | *cost per click*<br>indicates the amount paid (USD) for each click on the ad displayed for a given keyword<br> |
| `monthly_searches` | array | *monthly searches*<br>represents the (approximate) number of searches on this keyword idea (as available for the past twelve months), targeted to the specified geographic locations<br>if there is no data, the value is `null` |
| `year` | integer | *year* |
| `month` | integer | *month* |
| `search_volume` | integer | *monthly average search volume rate* |
| `keyword_annotations` | object | *the annotations for the keyword* |
| `concepts` | array | *the list of concepts for the keyword* |
| `name` | string | *the concept name for the keyword in the concept_group* |
| `concept_group` | object | *the concept group of the concept details* |
| `name` | string | *the concept group name* |
| `type` | string | *the concept group type* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Live
*Source: [https://docs.dataforseo.com/v3/keywords_data/google_ads/keywords_for_keywords/live/](https://docs.dataforseo.com/v3/keywords_data/google_ads/keywords_for_keywords/live/)*
#### Setting Live ‘Keywords For Keywords’ Tasks

Note that Google Ads Keywords Data API is based on the latest version of the [Google Ads API](https://developers.google.com/google-ads/api/docs/start) that has replaced legacy Google AdWords API. If you’re using [DataForSEO Google AdWords API](https://docs.dataforseo.com/v3/keywords_data/google/overview/?bash), you need to upgrade to [DataForSEO Google Ads API](https://docs.dataforseo.com/v3/keywords_data/google_ads/overview/?bash).

This endpoint will provide relevant keywords for the specified terms. Set up to 20 keywords in the `keywords` array and get keyword suggestions from Google Ads.

**Note: you can send no more than 12 requests per minute per account using Google Ads Live endpoints.**

Historical data is available for 4 years.

POSThttps://api.dataforseo.com/v3/keywords_data/google_ads/keywords_for_keywords/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/google-ads) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute. Visit [DataForSEO Help Center](https://dataforseo.com/help-center/best-practices-for-handling-keywords-data-api-requests) to get practical tips for request handling depending on your Keyword Data API payload volume.

You can get up to 20,000 keyword suggestions with all essential keyword data in response to one request. Your account will be charged for each request, no matter what number of keywords you receive in the result.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

optional field

| Field name | Type | Description |
| --- | --- | --- |
| `keywords` | array | *keywords*<br>**required field**<br>The maximum number of keywords you can specify: 20<br>The maximum number of characters for each keyword: 80<br>the keywords you specify will be converted to a lowercase format<br>**Note:** Google Ads may return no data for certain groups of keywords<br>[visit our Help Center to learn more](https://dataforseo.com/help-center/no-search-volume-data-for-some-keywords)<br>**Also note** that Google Ads doesn’t allow using certain symbols and characters (e.g., UTF symbols, emojis), so you can’t use them when setting a task;<br>to learn more about which symbols and characters can be used, please refer to [this article](https://dataforseo.com/help-center/using-symbols-in-keywords-when-setting-a-google-ads-task)<br>learn more about rules and limitations of `keyword` and `keywords` fields in DataForSEO APIs in this [Help Center article](https://dataforseo.com/help-center/rules-and-limitations-of-keyword-and-keywords-fields-in-dataforseo-apis) |
| `location_name` | string | *full name of search engine location*<br>optional field<br>if you do not indicate the location, you will receive worldwide results, i.e., for all available locations;<br>**if you use this field, you don’t need to specify `location_code` or `location_coordinate`**<br>you can receive the list of available locations of the search engine with their `location_name` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/google_ads/locations`<br>example:<br>`London,England,United Kingdom` |
| `location_code` | integer | *search engine location code*<br>optional field<br>if you do not indicate the location, you will receive worldwide results, i.e., for all available locations;<br>**if you use this field, you don’t need to specify `location_name` or `location_coordinate`**;<br>you can receive the list of available locations of the search engines with their `location_code` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/google_ads/locations`<br>example:<br>`2840` |
| `location_coordinate` | string | *GPS coordinates of a location*<br>optional field<br>if you do not indicate the location, you will receive worldwide results, i.e., for all available locations;<br>**if you use this field, you don’t need to specify `location_name` or `location_code`**;<br>`location_coordinate` parameter should be specified in the *“latitude,longitude”* format;<br>**the data will be provided for the country the specified coordinates belong to**;<br>example:<br>`52.6178549,-155.352142` |
| `language_name` | string | *full name of search engine language*<br>optional field<br>you can receive the list of available languages of the search engine with their `language_name` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/google_ads/languages`<br>example:<br>`English` |
| `language_code` | string | *search engine language code*<br>optional field<br>you can receive the list of available languages of the search engine with their `language_code` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/google_ads/languages`<br>example:<br>`en` |
| `search_partners` | boolean | *include Google search partners*<br>optional field<br>if you specify `true`, the results will be delivered for owned, operated, and syndicated networks across [Google and partner sites](https://support.google.com/google-ads/answer/1722047?hl=en) that host Google search;<br>default value: `false` – results are returned for Google search sites |
| `date_from` | string | *starting date of the time range*<br>optional field<br>date format: `"yyyy-mm-dd"`<br>minimal value: 4 years from the current date<br>by default, data is returned for the past 12 months;<br>**Note**: the indicated date cannot be greater than that specified in `date_to` and/or yesterday’s date;if [Status endpoint](https://docs.dataforseo.com/v3/keywords_data/google_ads/status/) returns `false` in the `actual_data` field, `date_from` can be set to the month before last and prior;<br>if [Status endpoint](https://docs.dataforseo.com/v3/keywords_data/google_ads/status/) returns `true` in the `actual_data` field, `date_from` can be set to the last month and prior |
| `date_to` | string | *ending date of the time range*<br>optional field<br>**Note:** the indicated date cannot be greater than yesterday’s date;<br>if you don’t specify this field, yesterday’s date will be used by default<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2022-11-30"` |
| `sort_by` | string | *results sorting parameters*<br>optional field<br>Use these parameters to sort the results by `relevance`, `search_volume`, `competition_index`, `low_top_of_page_bid`, or `high_top_of_page_bid` in descending order<br>default value: `relevance` |
| `include_adult_keywords` | boolean | *include keywords associated with adult content*<br>optional field<br>if set to `true`, adult keywords will be included in the response<br>default value: `false`<br>**note** that the API may return no data for such keywords due to [Google Ads restrictions](https://support.google.com/adspolicy/answer/6008942?hl=en) |
| `tag` | string | *user-defined task identifier*<br>optional field<br>*the character limit is 255*<br>you can use this parameter to identify the task and match it with the result<br>you will find the specified `tag` value in the `data` object of the response |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the result array:**

| `version` | string | *the current version of the API* |
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
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `keyword` | string | *keyword in a POST array* |
| `location_code` | integer | *location code in a POST array*<br>if there is no data, the value is `null` |
| `language_code` | string | *language code in a POST array*<br>if there is no data, the value is `null` |
| `search_partners` | boolean | *include Google search partners*<br>the value you specified when setting the task<br>if `true`, the results are returned for owned, operated, and syndicated networks across Google and partner sites that host Google search;<br>if `false`, the results are returned for Google search sites only |
| `competition` | string | *competition*<br>represents the relative level of competition associated with the given keyword in paid SERP only<br>possible values: `LOW`, `MEDIUM`, `HIGH`<br>if competition level is unknown, the value is `null`;<br>learn more about the metric in [this help center article](https://dataforseo.com/help-center/what-is-competition) |
| `competition_index` | integer | *competition index*<br>the competition index for the query indicating how competitive ad placement is for the keyword<br>can take values from 0 to 100<br>the level of competition from 0 to 100 is determined by the number of ad slots filled divided by the total number of ad slots available<br>if not enough data is available, the value is `null`;<br>learn more about the metric in [this help center article](https://dataforseo.com/help-center/what-is-competition) |
| `search_volume` | integer | *monthly average search volume rate*<br>represents the (approximate) number of searches for the given keyword idea either on google.com or google.com and partners, depending on the user’s targeting<br>if there is no data, the value is `null` |
| `low_top_of_page_bid` | float | *minimum bid for the ad to be displayed at the top of the first page*<br>indicates the value greater than about 20% of the lowest bids for which ads were displayed (based on Google Ads statistics for advertisers)<br>the value may differ depending on the location specified in a POST request |
| `high_top_of_page_bid` | float | *maximum bid for the ad to be displayed at the top of the first page*<br>indicates the value greater than about 80% of the lowest bids for which ads were displayed (based on Google Ads statistics for advertisers)<br>the value may differ depending on the location specified in a POST request |
| `cpc` | float | *cost per click*<br>indicates the amount paid (USD) for each click on the ad displayed for a given keyword<br> |
| `monthly_searches` | array | *monthly searches*<br>represents the (approximate) number of searches on this keyword idea (as available for the past twelve months), targeted to the specified geographic locations<br>if there is no data, the value is `null` |
| `year` | integer | *year* |
| `month` | integer | *month* |
| `search_volume` | integer | *monthly average search volume rate* |
| `keyword_annotations` | object | *the annotations for the keyword* |
| `concepts` | array | *the list of concepts for the keyword* |
| `name` | string | *the concept name for the keyword in the concept_group* |
| `concept_group` | object | *the concept group of the concept details* |
| `name` | string | *the concept group name* |
| `type` | string | *the concept group type* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Task POST
*Source: [https://docs.dataforseo.com/v3/keywords_data/google_ads/ad_traffic_by_keywords/task_post/](https://docs.dataforseo.com/v3/keywords_data/google_ads/ad_traffic_by_keywords/task_post/)*
#### Setting ‘Ad Traffic By Keywords’ Tasks

###### Please note that starting from June 1, Google Ad Traffic By Keywords returns bulk data for the entire campaign (all keywords specified when setting a task). You can learn more in [this update](https://dataforseo.com/update/changes-google-ad-traffic-by-keywords).

Note that Google Ads Keywords Data API is based on the latest version of the [Google Ads API](https://developers.google.com/google-ads/api/docs/start) that has replaced legacy Google AdWords API. If you’re using [DataForSEO Google AdWords API](https://docs.dataforseo.com/v3/keywords_data/google/overview/?bash), you need to upgrade to [DataForSEO Google Ads API](https://docs.dataforseo.com/v3/keywords_data/google_ads/overview/?bash).
 
Using the Ad Traffic By Keywords endpoint, you can receive a set of stats for estimating CPC, and clicks. This data is really useful for estimating real demand for a specific keyword, as it is much more accurate than the regular search volume information, which shows the broad match estimation for a group of similar keywords.

Note that Google Ads API provides account-specific results based on ad history, creatives already in the account, and other factors. Use high `bid` to level other factors.

The values you receive in the response depend on the set forecasting time period. There are two ways to specify the necessary time period:

1. By indicating the exact dates in the future using `date_from` and `date_to`;
2. By setting the `date_interval` to `next_week`, `next_month`, or `next_quarter`

If you do not use one of the ways above, the forecasting time period of `next_month` will be applied by default.

This endpoint uses the Standard method of data retrieval. If you don’t need to receive data in real-time, this method is the best option for you. Set a task and retrieve the results when our system collects them. Execution time depends on the system workload.

If your system requires delivering instant results, [the Live method](https://docs.dataforseo.com/v3/keywords_data/google_ads/ad_traffic_by_keywords/live/?php) will be a better solution. This method doesn’t require making separate POST and GET requests to the corresponding endpoints.

POSThttps://api.dataforseo.com/v3/keywords_data/google_ads/ad_traffic_by_keywords/task_post

Pricing

Your account will be charged only for setting a task.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/google-ads) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). Task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute, with each POST call containing no more than 100 tasks. If your POST call contains over 100 tasks, the tasks over this limit will return the `40006` error. Visit [DataForSEO Help Center](https://dataforseo.com/help-center/best-practices-for-handling-keywords-data-api-requests) to get practical tips for request handling depending on your Keyword Data API payload volume.

You can send up to 1000 keywords in one `keywords` array. Our system will charge your account per request, no matter what number of keywords an array has, the price for 1 or 1000 keywords will be the same.

You can also retrieve the results of completed tasks using the unique task identifier `id`. Alternatively, we can send them to you as soon as they are ready if you specify the `postback_url` or `pingback_url` when setting a task. Note that if your server doesn’t respond within 10 seconds, the connection will be aborted by timeout, and the task will be transferred to the [tasks_ready](https://docs.dataforseo.com/v3/keywords_data/google_ads/ad_traffic_by_keywords/tasks_ready/?php) list. The error code and message depend on your server’s configuration.

See [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) to learn more about using pingbacks and postbacks with DataForSEO APIs.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

optional field

| Field name | Type | Description |
| --- | --- | --- |
| `keywords` | array | *keywords*<br>**required field**<br>The maximum number of keywords you can specify: 1000<br>The maximum number of characters for each keyword: 80<br>The maximum number of words for each keyword phrase: 10<br>the keywords you specify will be converted to a lowercase format<br>**Note #1:** [Google Ads may return no data for certain groups of keywords](https://dataforseo.com/help-center/no-search-volume-data-for-some-keywords);<br>**Note #2:** [Google Ads provides combined search volume values for groups of similar keywords](https://dataforseo.com/help-center/sv-broad-exact-phrase-match)<br>to obtain search volume for similar keywords, we recommend submitting such keywords in separate requests;<br>**Note #3:** Google Ads doesn’t allow using certain symbols and characters (e.g., UTF symbols, emojis), so you can’t use them when setting a task;<br>to learn more about which symbols and characters can be used, please refer to [this article](https://dataforseo.com/help-center/using-symbols-in-keywords-when-setting-a-google-ads-task)<br>learn more about rules and limitations of `keyword` and `keywords` fields in DataForSEO APIs in this [Help Center article](https://dataforseo.com/help-center/rules-and-limitations-of-keyword-and-keywords-fields-in-dataforseo-apis) |
| `bid` | float | *the maximum custom bid*<br>**required field**<br>the collected data will be based on this value<br>it stands for the price you are willing to pay for an ad; the higher value you specify here, the higher values you will get in the returned metrics<br>learn more in [this help center article](https://dataforseo.com/help-center/configuring-bid) |
| `match` | string | *keywords match-type*<br>**required field**<br>can take the following values: `exact`, `broad`, `phrase` |
| `location_name` | string | *full name of search engine location*<br>optional field<br>if you do not indicate the location, you will receive worldwide results, i.e., for all available locations;<br>**if you use this field, you don’t need to specify `location_code` or `location_coordinate`**<br>you can receive the list of available locations of the search engine with their `location_name` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/google_ads/locations`<br>example:<br>`London,England,United Kingdom` |
| `location_code` | integer | *search engine location code*<br>optional field<br>if you do not indicate the location, you will receive worldwide results, i.e., for all available locations;<br>**if you use this field, you don’t need to specify `location_name` or `location_coordinate`**;<br>you can receive the list of available locations of the search engines with their `location_code` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/google_ads/locations`<br>example:<br>`2840` |
| `location_coordinate` | string | *GPS coordinates of a location*<br>optional field<br>if you do not indicate the location, you will receive worldwide results, i.e., for all available locations;<br>**if you use this field, you don’t need to specify `location_name` or `location_code`**;<br>`location_coordinate` parameter should be specified in the *“latitude,longitude”* format;<br>**the data will be provided for the country the specified coordinates belong to**;<br>example:<br>`52.6178549,-155.352142` |
| `language_name` | string | *full name of search engine language*<br>optional field<br>you can receive the list of available languages of the search engine with their `language_name` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/google_ads/languages`<br>example:<br>`English` |
| `language_code` | string | *search engine language code*<br>optional field<br>you can receive the list of available languages of the search engine with their `language_code` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/google_ads/languages`<br>example:<br>`en` |
| `date_from` | string | *starting date of the forecasting time range*<br>required field if you specify `date_to`<br>**if you indicate `date_from` and `date_to`, you don’t need to specify `date_interval`**<br>minimum value is tomorrow’s date<br>the value you specify in `date_from` shouldn’t be further than `date_to`<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2021-10-30"`if [Status endpoint](https://docs.dataforseo.com/v3/keywords_data/google_ads/status/) returns `false` in the `actual_data` field, `date_from` can be set to the month before last and prior;<br>if [Status endpoint](https://docs.dataforseo.com/v3/keywords_data/google_ads/status/) returns `true` in the `actual_data` field, `date_from` can be set to the last month and prior |
| `date_to` | string | *ending date of the forecasting time range*<br>required field if you specify `date_from`<br>**if you indicate `date_from` and `date_to`, you don’t need to specify `date_interval`**<br>minimum value is `date_from` +1 day<br>maximum value is current day and month of the next year<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2022-10-30"` |
| `date_interval` | string | *forecasting date interval*<br>optional field<br>**if you specify `date_interval`, you don’t need to indicate `date_from` and `date_to`**<br>possible values: `next_week`, `next_month`, `next_quarter`<br>default value: `next_month` |
| `sort_by` | string | *results sorting parameters*<br>optional field<br>Use these parameters to sort the results by `relevance`, `average_cpc`, `cost`, or `clicks` in the descending order<br>default value: `relevance` |
| `postback_url` | string | *URL for sending task results*<br>optional field<br>once the task is completed, we will send a POST request with its results compressed in the `gzip` format to the `postback_url` you specified<br>you can use the ‘$id’ string as a `$id` variable and ‘$tag’ as urlencoded `$tag` variable. We will set the necessary values before sending the request.<br>example:<br>`http://your-server.com/postbackscript?id=$id`<br>`http://your-server.com/postbackscript?id=$id&tag=$tag`<br>**Note:** special characters in `postback_url` will be urlencoded;<br>i.a., the `#` character will be encoded into `%23`<br>learn more on our [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) |
| `pingback_url` | string | *notification URL of a completed task*<br>optional field<br>when a task is completed we will notify you by GET request sent to the URL you have specified<br>you can use the ‘$id’ string as a `$id` variable and ‘$tag’ as urlencoded `$tag` variable. We will set the necessary values before sending the request.<br>example:<br>`http://your-server.com/pingscript?id=$id`<br>`http://your-server.com/pingscript?id=$id&tag=$tag`<br>**Note:** special characters in `pingback_url` will be urlencoded;<br>i.a., the `#` character will be encoded into `%23`<br>learn more on our [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) |
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
| `tasks_count` | integer | *the number of tasks in the **`tasks`**array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *unique task identifier in our system*<br>in the [Universally unique identifier (UUID)](https://en.wikipedia.org/wiki/Universally_unique_identifier) format |
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
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
*Source: [https://docs.dataforseo.com/v3/keywords_data/google_ads/ad_traffic_by_keywords/tasks_ready/](https://docs.dataforseo.com/v3/keywords_data/google_ads/ad_traffic_by_keywords/tasks_ready/)*
#### Get ‘Ad Traffic By Keywords’ Completed Tasks

This endpoint is designed to provide you with a list of completed tasks, which haven’t been collected yet. If you use the Standard method without specifying the `postback_url`, you can receive the list of `id` for all completed tasks using this endpoint. Then, you can collect the results using the **‘Task GET’** endpoint.

Learn more about task completion and obtaining a list of completed tasks in [this help center article.](https://dataforseo.com/help-center/completed-tasks)

**Note:** due to the peculiarities of our architecture the queue of completed tasks is updated with a small delay, which can be an issue for high-volume users. If your system requires collecting over 1000 tasks a minute, we recommend using [pingbacks/postbacks](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) instead, and applying the Tasks Ready endpoint only to obtain the IDs of failed postback tasks.

GEThttps://api.dataforseo.com/v3/keywords_data/google_ads/ad_traffic_by_keywords/tasks_ready

Pricing

Your account will not be charged when receiving results

Each separate task will remain on the list until it is collected. You can make **up to 20 API calls per minute.** With each API call, you can get 1000 tasks completed within three previous days. The list will not contain the tasks which have already been collected and the tasks that were not collected **within the three days** after completion.

Please note that if you specify the `postback_url`, the task will not be in the list of completed tasks. The task can only be found in the list if the request to your server failed, and your server returned HTTP code response less than `200` or higher than `300`.

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
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the parameters passed in the request’s URL* |
| ** `result`** | array | *array of results* |
| `id` | string | *task identifier of the completed task*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `se` | string | *search engine specified when setting the task* |
| `function` | string | *type of the task* |
| `date_posted` | string | *date when the task was posted (in the UTC format)* |
| `endpoint` | string | *URL for collecting the results of the task* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Task GET
*Source: [https://docs.dataforseo.com/v3/keywords_data/google_ads/ad_traffic_by_keywords/task_get/](https://docs.dataforseo.com/v3/keywords_data/google_ads/ad_traffic_by_keywords/task_get/)*
#### Get ‘Ads Traffic By Keywords’ Results by id

###### Please note that starting from June 1, Google Ad Traffic By Keywords returns bulk data for the entire campaign (all keywords specified when setting a task). You can learn more in [this update](https://dataforseo.com/update/changes-google-ad-traffic-by-keywords).

Note that Google Ads Keywords Data API is based on the latest version of the [Google Ads API](https://developers.google.com/google-ads/api/docs/start) that has replaced legacy Google AdWords API. If you’re using [DataForSEO Google AdWords API](https://docs.dataforseo.com/v3/keywords_data/google/overview/?bash), you need to upgrade to [DataForSEO Google Ads API](https://docs.dataforseo.com/v3/keywords_data/google_ads/overview/?bash).

Using the Ad Traffic By Keywords endpoint, you can receive a set of stats for estimating CPC, and clicks. This data is really useful for estimating real demand for a specific keyword, as it is much more accurate than the regular search volume information, which shows the broad match estimation for a group of similar keywords.

GEThttps://api.dataforseo.com/v3/keywords_data/google_ads/ad_traffic_by_keywords/task_get/$id

Pricing

Your account will be charged only for posting a task. You can get the results of the task within the next 30 days for free.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/google-ads) page.

**Description of the fields for sending a request:**

| Field name | Type | Description |
| --- | --- | --- |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format**<br>you will be able to use it within **30 days** to request the results of the task at any time |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the result array:**

| `version` | string | *the current version of the API* |
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
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `keyword` | string | *keyword in a POST array*<br>metrics are provided for all the keywords specified in the POST array |
| `location_code` | integer | *location code in a POST array*<br>if there is no data, then the value is `null` |
| `language_code` | string | *language code in a POST array*<br>if there is no data, then the value is `null` |
| `date_interval` | string | *forecasting date interval in a POST array* |
| `search_partners` | boolean | *include Google search partners*<br>the value is always `false`<br> |
| `bid` | float | *the maximum custom bid*<br>the bid you have specified when setting the task<br>represents the price you are willing to pay for an ad<br>the higher value you have specified, the higher metrics and cost you receive in response<br>learn more in [this help center article](https://dataforseo.com/help-center/configuring-bid) |
| `match` | string | *keywords match-type*<br>can take the following values: `exact`, `broad`, `phrase` |
| `impressions` | float | *projected number of ad impressions*<br>number of impressions an ad is projected to get within the specified time period<br>**Note:** parameter deprecated, the value is always `null`<br> |
| `ctr` | float | *projected clickthrough rate (CTR) of the advertisement*<br>number of clicks an ad is projected to receive divided by the number of ad impressions;<br>**Note:** parameter deprecated, the value is always `null`<br> |
| `average_cpc` | float | *the average cost-per-click value*<br>represents the cost-per-click (USD) estimated for a keyword based on the specified time period and historical data;<br>if there is no data, then the value is `null` |
| `cost` | float | *charge for an ad*<br>amount that will be charged for running an ad within the specified time period<br>if there is no data, then the value is `null` |
| `clicks` | float | *number of clicks on an ad*<br>number of clicks an ad is projected to get within the specified time period<br>if there is no data, then the value is `null` |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Live
*Source: [https://docs.dataforseo.com/v3/keywords_data/google_ads/ad_traffic_by_keywords/live/](https://docs.dataforseo.com/v3/keywords_data/google_ads/ad_traffic_by_keywords/live/)*
#### Setting Live ‘Ad Traffic By Keywords’ Tasks

###### Please note that starting from June 1, Google Ad Traffic By Keywords returns bulk data for the entire campaign (all keywords specified when setting a task). You can learn more in [this update](https://dataforseo.com/update/changes-google-ad-traffic-by-keywords).

Note that Google Ads Keywords Data API is based on the latest version of the [Google Ads API](https://developers.google.com/google-ads/api/docs/start) that has replaced legacy Google AdWords API. If you’re using [DataForSEO Google AdWords API](https://docs.dataforseo.com/v3/keywords_data/google/overview/?bash), you need to upgrade to [DataForSEO Google Ads API](https://docs.dataforseo.com/v3/keywords_data/google_ads/overview/?bash).
 
**Note: you can send no more than 12 requests per minute per account using Google Ads Live endpoints.**

Using the Ad Traffic By Keywords endpoint, you can receive a set of stats for estimating impressions, CPC, and clicks. This data is really useful for estimating real demand for a specific keyword, as it is much more accurate than the regular search volume information, which shows the broad match estimation for a group of similar keywords.

Note that Google Ads API provides account-specific results based on ad history, creatives already in the account, and other factors. Use high `bid` to level other factors.

The values you receive in the response depend on the set forecasting time period. There are two ways to specify the necessary time period:

1. By indicating the exact dates in the future using `date_from` and `date_to`;
2. By setting the `date_interval` to `next_week`, `next_month`, or `next_quarter`

If you do not use one of the ways above, the forecasting time period of `next_month` will be applied by default.

POSThttps://api.dataforseo.com/v3/keywords_data/google_ads/ad_traffic_by_keywords/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/google-ads) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute. Visit [DataForSEO Help Center](https://dataforseo.com/help-center/best-practices-for-handling-keywords-data-api-requests) to get practical tips for request handling depending on your Keyword Data API payload volume.

You can send up to 1000 keywords in one `keywords` array. Our system will charge your account per request, no matter what number of keywords an array has, the price for 1 or 1000 keywords will be the same.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

optional field

| Field name | Type | Description |
| --- | --- | --- |
| `keywords` | array | *keywords*<br>**required field**<br>The maximum number of keywords you can specify: 1000<br>The maximum number of characters for each keyword: 80<br>The maximum number of words for each keyword phrase: 10<br>the keywords you specify will be converted to a lowercase format<br>**Note:** Google Ads may return no data for certain groups of keywords<br>[visit our Help Center to learn more](https://dataforseo.com/help-center/no-search-volume-data-for-some-keywords)<br>**Also note** that Google Ads doesn’t allow using certain symbols and characters (e.g., UTF symbols, emojis), so you can’t use them when setting a task;<br>to learn more about which symbols and characters can be used, please refer to [this article](https://dataforseo.com/help-center/using-symbols-in-keywords-when-setting-a-google-ads-task)<br>learn more about rules and limitations of `keyword` and `keywords` fields in DataForSEO APIs in this [Help Center article](https://dataforseo.com/help-center/rules-and-limitations-of-keyword-and-keywords-fields-in-dataforseo-apis) |
| `bid` | integer | *the maximum custom bid*<br>**required field**<br>the collected data will be based on this value<br>it stands for the price you are willing to pay for an ad; the higher value you specify here, the higher values you will get in the returned metrics<br>learn more in [this help center article](https://dataforseo.com/help-center/configuring-bid) |
| `match` | string | *keywords match-type*<br>**required field**<br>can take the following values: `exact`, `broad`, `phrase` |
| `location_name` | string | *full name of search engine location*<br>optional field<br>if you do not indicate the location, you will receive worldwide results, i.e., for all available locations;<br>**if you use this field, you don’t need to specify `location_code` or `location_coordinate`**<br>you can receive the list of available locations of the search engine with their `location_name` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/google_ads/locations`<br>example:<br>`London,England,United Kingdom` |
| `location_code` | integer | *search engine location code*<br>optional field<br>if you do not indicate the location, you will receive worldwide results, i.e., for all available locations;<br>**if you use this field, you don’t need to specify `location_name` or `location_coordinate`**;<br>you can receive the list of available locations of the search engines with their `location_code` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/google_ads/locations`<br>example:<br>`2840` |
| `location_coordinate` | string | *GPS coordinates of a location*<br>optional field<br>if you do not indicate the location, you will receive worldwide results, i.e., for all available locations;<br>**if you use this field, you don’t need to specify `location_name` or `location_code`**;<br>`location_coordinate` parameter should be specified in the *“latitude,longitude”* format;<br>**the data will be provided for the country the specified coordinates belong to**;<br>example:<br>`52.6178549,-155.352142` |
| `language_name` | string | *full name of search engine language*<br>optional field<br>you can receive the list of available languages of the search engine with their `language_name` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/google_ads/languages`<br>example:<br>`English` |
| `language_code` | string | *search engine language code*<br>optional field<br>you can receive the list of available languages of the search engine with their `language_code` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/google_ads/languages`<br>example:<br>`en` |
| `date_from` | string | *starting date of the forecasting time range*<br>required field if you specify `date_to`<br>**if you indicate `date_from` and `date_to`, you don’t need to specify `date_interval`**<br>minimum value is tomorrow’s date<br>the value you specify in `date_from` shouldn’t be further than `date_to`<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2021-10-30"`if [Status endpoint](https://docs.dataforseo.com/v3/keywords_data/google_ads/status/) returns `false` in the `actual_data` field, `date_from` can be set to the month before last and prior;<br>if [Status endpoint](https://docs.dataforseo.com/v3/keywords_data/google_ads/status/) returns `true` in the `actual_data` field, `date_from` can be set to the last month and prior |
| `date_to` | string | *ending date of the forecasting time range*<br>required field if you specify `date_from`<br>**if you indicate `date_from` and `date_to`, you don’t need to specify `date_interval`**<br>minimum value is `date_from` +1 day<br>maximum value is current day and month of the next year<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2022-10-30"` |
| `date_interval` | string | *forecasting date interval*<br>optional field<br>**if you specify `date_interval`, you don’t need to indicate `date_from` and `date_to`**<br>possible values: `next_week`, `next_month`, `next_quarter`<br>default value: `next_month` |
| `sort_by` | string | *results sorting parameters*<br>optional field<br>Use these parameters to sort the results by `relevance`, `impressions`, `ctr`, `average_cpc`, `cost`, or `clicks` in the descending order<br>default value: `relevance` |
| `tag` | string | *user-defined task identifier*<br>optional field<br>*the character limit is 255*<br>you can use this parameter to identify the task and match it with the result<br>you will find the specified `tag` value in the `data` object of the response |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the result array:**

| `version` | string | *the current version of the API* |
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
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `keyword` | string | *keyword in a POST array* |
| `location_code` | integer | *location code in a POST array*<br>if there is no data, then the value is `null` |
| `language_code` | string | *language code in a POST array*<br>if there is no data, then the value is `null` |
| `date_interval` | string | *forecasting date interval in a POST array* |
| `search_partners` | boolean | *include Google search partners*<br>the value you specified when setting the task<br>**Note:** parameter deprecated, the value is always `false` |
| `bid` | integer | *the maximum custom bid*<br>the bid you have specified when setting the task<br>represents the price you are willing to pay for an ad<br>the higher value you have specified, the higher metrics and cost you receive in response<br>learn more in [this help center article](https://dataforseo.com/help-center/configuring-bid) |
| `match` | string | *keywords match-type*<br>can take the following values: `exact`, `broad`, `phrase` |
| `impressions` | float | *projected number of ad impressions*<br>number of impressions an ad is projected to get within the specified time period<br>**Note:** parameter deprecated, the value is always `null` |
| `ctr` | float | *projected click through rate (CTR) of the advertisement*<br>number of clicks an ad is projected to receive divided by the number of ad impressions; the CTR is projected for the specified time period<br>**Note:** parameter deprecated, the value is always `null` |
| `average_cpc` | float | *the average cost-per-click value*<br>represents the cost-per-click (USD) estimated for a keyword based on the specified time period and historical data;<br>if there is no data, then the value is `null` |
| `cost` | float | *charge for an ad*<br>amount that will be charged for running an ad within the specified time period<br>if there is no data, then the value is `null` |
| `clicks` | float | *number of clicks on an ad*<br>number of clicks an ad is projected to get within the specified time period<br>if there is no data, then the value is `null` |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


#### Overview
*Source: [https://docs.dataforseo.com/v3/keywords_data/bing/overview/](https://docs.dataforseo.com/v3/keywords_data/bing/overview/)*
### Bing Keywords Data API: Overview

This API is the ultimate source of data for keyword analysis

**Bing Keywords Data API** will provide you with:

- [Search Volume](https://docs.dataforseo.com/v3/keywords_data/bing/search_volume/live/)
- [Keywords For Site](https://docs.dataforseo.com/v3/keywords_data/bing/keywords_for_site/live/)
- [Audience Estimation](https://docs.dataforseo.com/v3/keywords_data/bing/audience_estimation/live/)

- [Keywords For Keywords](https://docs.dataforseo.com/v3/keywords_data/bing/keywords_for_keywords/live/)
- [Keyword Performance](https://docs.dataforseo.com/v3/keywords_data/bing/keyword_performance/live/)
- [Keyword Suggestions For URL](https://docs.dataforseo.com/v3/keywords_data/bing/keyword_suggestions_for_url/live/)

The returned results are specific to the indicated [language](https://docs.dataforseo.com/v3/keywords_data/bing/languages/) and [location](https://docs.dataforseo.com/v3/keywords_data/bing/locations/) parameters. We use [Bing Ads API](https://docs.microsoft.com/en-us/advertising/ad-insight-service/getkeywordideas) as a data source. Thus, the locations supported in Bing Ads API are identical to the datasource.

Subsequently, the restrictions of Bing endpoints in Keywords Data API are related to [Microsoft Advertising Policies and Guidelines](https://about.ads.microsoft.com/en-us/resources/policies). We are not able to return data for keywords that fall into such categories as weapons, tobacco, drugs, violence, terrorism, etc.

Please note that if you post, for instance, 100 keywords in a batch and at least one of them falls into one of the categories listed above, no data will be retrieved for the whole batch of keywords.

Note that it can take up to 72 hours before the keyword data for the previous calendar month is available. For example, if you request keyword data on August 1st, 2nd or 3rd, and data for July is not available yet, you will receive the data for June.

##### Methods

The cost of using Keywords Data endpoints depends on the selected method and priority of task execution. Available methods and priorities are described below.

DataForSEO has two main methods to deliver the results: Standard and Live.

If your system requires delivering instant results, **the Live method** is the best solution for you. Unlike the Standard method, this method doesn’t require making separate POST and GET requests to the corresponding endpoints.

If you don’t need to receive data in real-time, you can use **the Standard method** of data retrieval. This method requires making separate POST and GET requests, but it’s more affordable. Using this method, you can retrieve the results after our system collects them.

Alternatively, you can specify `pingback_url` or `postback_url` when setting a task, and we will notify you on completion of tasks or send them to you respectively.

If you need to set several tasks, you can receive the list of `id` for all completed tasks using **‘Tasks Ready’ endpoint**, and then collect the results of each separate task using ‘Task GET’ endpoint.

Learn more about task completion and obtaining a list of completed tasks in [this help center article.](https://dataforseo.com/help-center/completed-tasks)

You can send up to 2000 API calls per minute. Contact us if you would like to raise the limit.

Visit [DataForSEO Help Center](https://dataforseo.com/help-center/best-practices-for-handling-keywords-data-api-requests) to get practical tips for request handling depending on your Keyword Data API payload volume.

##### Cost

The price depends on the method of data retrieval. The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/bing-ads) page.

You can test Keywords Data API for free using DataForSEO [Sandbox.](https://docs.dataforseo.com/v3/appendix/sandbox/)

---


#### Locations
*Source: [https://docs.dataforseo.com/v3/keywords_data/bing/locations/](https://docs.dataforseo.com/v3/keywords_data/bing/locations/)*
#### List of Bing Locations for Keywords Data

By calling this API you will receive the list of locations supported in Bing Ads API.

##### **Note:** All locations in Russia and Belarus are no longer supported across all DataForSEO services due to the invasion of Ukraine.

You can also [download the full list of supported locations](https://cdn.dataforseo.com/v3/locations/locations_kwrd_bing_2026_06_10.csv) in the CSV format (last updated 2026-06-10).

Note that [Keyword Performance](https://docs.dataforseo.com/v3/keywords_data/bing/keyword_performance/live/?php) endpoints of Bing Ads API have a different [list of available locations and languages](https://docs.dataforseo.com/v3/keywords_data/bing/keyword_performance/locations_and_languages/).

GEThttps://api.dataforseo.com/v3/keywords_data/bing/locations

Pricing

Your account will not be charged for using this API

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information about available locations.

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
| `location_code_parent` | integer | *the code of the superordinate location*<br>example:<br>`"location_code": 9041134,<br>"location_name": "Vienna International Airport,Lower Austria,Austria",<br>"location_code_parent": 20044`where `location_code_parent` corresponds to:<br>`"location_code": 20044,<br>"location_name": "Lower Austria,Austria"` |
| `country_iso_code` | string | *ISO country code of the location* |
| `location_type` | string | *location type*<br> |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


#### Languages
*Source: [https://docs.dataforseo.com/v3/keywords_data/bing/languages/](https://docs.dataforseo.com/v3/keywords_data/bing/languages/)*
#### List of Bing Languages for Keywords Data

Pricing

Your account will not be charged for using this API

GEThttps://api.dataforseo.com/v3/keywords_data/bing/languages

By calling this API you will receive the list of languages supported by Bing Ads API.

Note that [Keyword Performance](https://docs.dataforseo.com/v3/keywords_data/bing/keyword_performance/live/?php) endpoints of Bing Ads API have a different [list of available locations and languages](https://docs.dataforseo.com/v3/keywords_data/bing/keyword_performance/locations_and_languages/).

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information about available languages.

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
| `language_name` | string | *language name* |
| `language_code` | string | *language code according to [ISO 639-1](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes)* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Task POST
*Source: [https://docs.dataforseo.com/v3/keywords_data/bing/search_volume/task_post/](https://docs.dataforseo.com/v3/keywords_data/bing/search_volume/task_post/)*
#### Setting ‘Search Volume’ Tasks

This endpoint will provide you with search volume data for the last month, search volume trend for up to 24 past months (that will let you estimate search volume dynamics), current cost-per-click and competition values for paid search.

This is the Standard method of data retrieval. If you don’t need to receive data in real-time, this method is the best option for you. Set a task and retrieve the results when our system collects them. Execution time depends on the system workload.

If your system requires delivering instant results, [the Live method](https://docs.dataforseo.com/v3/keywords_data/bing/search_volume/live/) will be a better solution. This method doesn’t require making separate POST and GET requests to the corresponding endpoints.

Historical data is available for 24 months.

POSThttps://api.dataforseo.com/v3/keywords_data/bing/search_volume/task_post

Pricing

Your account will be charged only for setting a task.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/bing-ads) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). Task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute, with each POST call containing no more than 100 tasks. If your POST call contains over 100 tasks, the tasks over this limit will return the `40006` error. Visit [DataForSEO Help Center](https://dataforseo.com/help-center/best-practices-for-handling-keywords-data-api-requests) to get practical tips for request handling depending on your Keyword Data API payload volume.

You will get information for every single keyword in an array.

You can send up to 1000 keywords in one `keywords` array. Our system will charge your account per request, no matter what number of keywords an array has, the price for 1 or 1000 keywords will be the same.

You can also retrieve the results of completed tasks using the unique task identifier `id`. Alternatively, we can send them to you as soon as they are ready if you specify the `postback_url` or `pingback_url` when setting a task. Note that if your server doesn’t respond within 10 seconds, the connection will be aborted by timeout, and the task will be transferred to the [tasks_ready](https://docs.dataforseo.com/v3/keywords_data/bing/search_volume/tasks_ready/?php) list. The error code and message depend on your server’s configuration.

See [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) to learn more about using pingbacks and postbacks with DataForSEO APIs.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `keywords` | array | *keywords*<br>**required field**<br>The maximum number of keywords you can specify: 1000<br>The maximum number of characters for each keyword: 100<br>the specified keywords will be converted to lowercase, data will be provided in a separate array<br>learn more about rules and limitations of `keyword` and `keywords` fields in DataForSEO APIs in this [Help Center article](https://dataforseo.com/help-center/rules-and-limitations-of-keyword-and-keywords-fields-in-dataforseo-apis) |
| `location_name` | string | *full name of search engine location*<br>**required field if you don’t specify** `location_code` or `location_coordinate`<br>**if you use this field, you don’t need to specify `location_code` or `location_coordinate`**<br>you can receive the list of available locations of the search engine with their `location_name` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/bing/locations`<br>example:<br>`London,England,United Kingdom` |
| `location_code` | integer | *search engine location code*<br>**required field if you don’t specify** `location_name` or `location_coordinate`<br>**if you use this field, you don’t need to specify `location_name` or `location_coordinate`**<br>you can receive the list of available locations of the search engines with their `location_code` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/bing/locations`<br>example:<br>`2840` |
| `location_coordinate` | string | *GPS coordinates of a location*<br>**required field if you don’t specify** `location_name` or `location_code`<br>**if you use this field, you don’t need to specify `location_name` or `location_code`**<br>`location_coordinate` parameter should be specified in the *“latitude,longitude”* format<br>**the data will be provided for the country the specified coordinates belong to**<br>example:<br>`52.6178549,-155.352142` |
| `language_name` | string | *full name of search engine language*<br>**required field if you don’t specify** `language_code`<br>if you use this field, you don’t need to specify `language_code`<br>supported languages:<br>`English`, `French`, `German` |
| `language_code` | string | *search engine language code*<br>**required field if you don’t specify** `language_name`<br>if you use this field, you don’t need to specify `language_name`<br>supported languages:<br>`en`, `fr`, `de` |
| `device` | string | *device type*<br>optional field<br>specify this field if you want to get the data for a particular device typepossible values: `all`, `mobile`, `desktop`, `tablet`<br>default value: `all` |
| `sort_by` | string | *results sorting parameters*<br>optional field<br>Use these parameters to sort the results by `search_volume`, `cpc`, `competition` or `relevance` in the descending order<br>default value: `relevance` |
| `date_from` | string | *starting date of the time range*<br>optional field<br>if you don’t specify this field, data will be provided for the last 12 months<br>minimal value: 24 months from today’s date<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2020-01-01"`<br>**Note:** we do not recommend using a custom time range for the past year’s dates |
| `date_to` | string | *ending date of the time range*<br>optional field<br>if you don’t specify this field, data will be provided for the last 12 months;<br>minimum value: two years back from today’s date;<br>maximum value: one month from today’s date;<br>**note:** we do not recommend using a custom time range for the past year’s dates;<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2020-03-15"`<br>**Note:** we do not recommend using a custom time range for the past year’s dates |
| `postback_url` | string | *URL for sending task results*<br>optional field<br>once the task is completed, we will send a POST request with its results compressed in the `gzip` format to the `postback_url` you specified<br>you can use the ‘$id’ string as a `$id` variable and ‘$tag’ as urlencoded `$tag` variable. We will set the necessary values before sending the request.<br>example:<br>`http://your-server.com/postbackscript?id=$id`<br>`http://your-server.com/postbackscript?id=$id&tag=$tag`<br>**Note:** special characters in `postback_url` will be urlencoded;<br>i.a., the `#` character will be encoded into `%23`<br>learn more on our [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) |
| `pingback_url` | string | *notification URL of a completed task*<br>optional field<br>when a task is completed we will notify you by GET request sent to the URL you have specified<br>you can use the ‘$id’ string as a `$id` variable and ‘$tag’ as urlencoded `$tag` variable. We will set the necessary values before sending the request<br>example:<br>`http://your-server.com/pingscript?id=$id`<br>`http://your-server.com/pingscript?id=$id&tag=$tag`<br>**Note:** special characters in `pingback_url` will be urlencoded;<br>i.a., the `#` character will be encoded into `%23`<br>learn more on our [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) |
| `search_partners` | boolean | *Bing search partners type*<br>optional field<br>if you specify `true`, the results will be delivered for owned, operated, and syndicated networks across Bing, Yahoo, AOL and partner sites that host Bing, AOL, and Yahoo search.<br>default value: `false` – results are returned for Bing, AOL, and Yahoo search networks |
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
*Source: [https://docs.dataforseo.com/v3/keywords_data/bing/search_volume/tasks_ready//](https://docs.dataforseo.com/v3/keywords_data/bing/search_volume/tasks_ready//)*
#### Get ‘Search Volume’ Completed Tasks

This endpoint is designed to provide you with the list of completed tasks, which haven’t been collected yet. If you use the Standard method without specifying the `postback_url`, you can receive the list of `id` for all completed tasks using this endpoint. Then, you can collect the results using the **‘Task GET’** endpoint.

Learn more about task completion and obtaining a list of completed tasks in [this help center article.](https://dataforseo.com/help-center/completed-tasks)

**Note:** due to the peculiarities of our architecture the queue of completed tasks is updated with a small delay, which can be an issue for high-volume users. If your system requires collecting over 1000 tasks a minute, we recommend using [pingbacks/postbacks](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) instead, and applying the Tasks Ready endpoint only to obtain the IDs of failed postback tasks.

GEThttps://api.dataforseo.com/v3/keywords_data/bing/search_volume/tasks_ready

Pricing

Your account will not be charged when receiving results

Each separate task will remain on the list until it is collected. You can make **up to 20 API calls per minute.** With each API call, you can get 1000 tasks completed within three previous days. The list will not contain the tasks which have already been collected and the tasks that were not collected **within the three days** after completion.

Please note that if you specify the `postback_url`, the task will not be in the list of completed tasks. The task can only be found in the list if the request to your server failed, and your server returned HTTP code response less than `200` or higher than `300`.

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
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the parameters passed in the request’s URL* |
| ** `result`** | array | *array of results* |
| `id` | string | *task identifier of the completed task*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `se` | string | *search engine specified when setting the task* |
| `function` | string | *type of the task* |
| `date_posted` | string | *date when the task was posted (in the UTC format)* |
| `endpoint` | string | *URL for collecting the results of the task* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Task GET
*Source: [https://docs.dataforseo.com/v3/keywords_data/bing/search_volume/task_get/](https://docs.dataforseo.com/v3/keywords_data/bing/search_volume/task_get/)*
#### Get Search Volume Results by id

This endpoint will provide you with search volume data for the last month, search volume trend for the last year (that will let you estimate search volume dynamics), current cost-per-click and competition values for paid search.

GEThttps://api.dataforseo.com/v3/keywords_data/bing/search_volume/task_get/$id

Pricing

Your account will be charged only for posting a task. You can get the results of the task within the next 30 days for free.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/bing-ads) page.

**Description of the fields for sending a request:**

| Field name | Type | Description |
| --- | --- | --- |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format**<br>you will be able to use it within **30 days** to request the results of the task at any time |

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
| `status_code` | integer | *status code of the task *<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request<br>* |
| **`result`** | array | *array of results* |
| `keyword` | string | *keyword in a POST array* |
| `location_code` | integer | *location code in a POST array*<br> |
| `language_code` | string | *language code in a POST array*<br> |
| `search_partners` | boolean | *indicates whether data from partner networks included in the response*<br> |
| `device` | string | *device type in a POST array*<br>if there is no data, then the value is `null` |
| `competition` | float | *competition*<br>represents the relative amount of competition associated with the given keyword in paid SERP only. This value is based on Bing Ads data.<br>Possible values: `0.1`, `0.5`,`0.9`<br>`0.1` – low competition,<br>`0.5` – medium competition,<br>`0.9` – high competition;<br>if there is no data the value is `null` |
| `cpc` | float | *cost-per-click*<br>represents the average cost per click (USD) historically paid for the keyword.<br>if there is no data then the value is `null` |
| `search_volume` | integer | *monthly average search volume rate<br>*represents either the (approximate) number of searches for the given keyword idea on bing search engine, depending on the user’s targeting<br>search volume is rounded to the nearest tens<br>if there is no data then the value is `null` |
| `categories` | array | *product and service categories*<br>our API doesn’t return categories for this endpoint: the parameter will always equal `null`<br> |
| `monthly_searches` | array | *monthly searches*<br>represents the (approximate) number of searches on this keyword idea (as available for the past twelve months), targeted to the specified geographic locations<br>if there is no data then the value is `null` |
| `year` | integer | *year* |
| `month` | integer | *month* |
| `search_volume` | integer | *monthly average search volume rate*<br>search volume is rounded to the nearest tens<br> |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Live
*Source: [https://docs.dataforseo.com/v3/keywords_data/bing/search_volume/live/](https://docs.dataforseo.com/v3/keywords_data/bing/search_volume/live/)*
#### Setting Live ‘Search Volume’ Tasks

This endpoint will provide you with search volume data for the last month, search volume trend for up to 24 past months (that will let you estimate search volume dynamics), current cost-per-click and competition values for paid search.

If your system requires delivering instant results, the Live method is the best solution for you. Unlike the Standard method, this method doesn’t require making separate POST and GET requests to the corresponding endpoints.

If you don’t need to receive data in real-time, you can use the [Standard method](https://docs.dataforseo.com/v3/keywords_data/bing/search_volume/task_post/) of data retrieval. This method requires making separate POST and GET requests, but it’s more affordable. Using this method you can retrieve the results after our system collects them.

Historical data is available for 24 months.

POSThttps://api.dataforseo.com/v3/keywords_data/bing/search_volume/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/bing-ads) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute. Visit [DataForSEO Help Center](https://dataforseo.com/help-center/best-practices-for-handling-keywords-data-api-requests) to get practical tips for request handling depending on your Keyword Data API payload volume.

You will get information for every single keyword in an array.

You can send up to 1000 keywords in one `keywords` array. Our system will charge your account per each request, no matter what number of keywords an array has, the price for 1 or 1000 keywords will be the same.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `keywords` | array | *keywords*<br>**required field**<br>The maximum number of keywords you can specify: 1000<br>The maximum number of characters for each keyword: 100<br>the specified keywords will be converted to lowercase, data will be provided in a separate array<br>learn more about rules and limitations of `keyword` and `keywords` fields in DataForSEO APIs in this [Help Center article](https://dataforseo.com/help-center/rules-and-limitations-of-keyword-and-keywords-fields-in-dataforseo-apis) |
| `location_name` | string | *full name of search engine location*<br>**required field if you don’t specify** `location_code` or `location_coordinate`<br>**if you use this field, you don’t need to specify `location_code` or `location_coordinate`**<br>you can receive the list of available locations of the search engine with their `location_name` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/bing/locations`<br>example:<br>`London,England,United Kingdom` |
| `location_code` | integer | *search engine location code*<br>**required field if you don’t specify** `location_name` or `location_coordinate`<br>**if you use this field, you don’t need to specify `location_name` or `location_coordinate`**<br>you can receive the list of available locations of the search engines with their `location_code` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/bing/locations`<br>example:<br>`2840` |
| `location_coordinate` | string | *GPS coordinates of a location*<br>**required field if you don’t specify** `location_name` or `location_code`<br>**if you use this field, you don’t need to specify `location_name` or `location_code`**<br>`location_coordinate` parameter should be specified in the *“latitude,longitude”* format<br>**the data will be provided for the country the specified coordinates belong to**<br>example:<br>`52.6178549,-155.352142` |
| `language_name` | string | *full name of search engine language*<br>**required field if you don’t specify** `language_code`<br>if you use this field, you don’t need to specify `language_code`<br>supported languages:<br>`English`, `French`, `German` |
| `language_code` | string | *search engine language code*<br>**required field if you don’t specify** `language_name`<br>if you use this field, you don’t need to specify `language_name`<br>supported languages:<br>`en`, `fr`, `de` |
| `device` | string | *device type*<br>optional field<br>specify this field if you want to get the data for a particular device type;<br>possible values: `all`, `mobile`, `desktop`, `tablet`<br>default value: `all` |
| `sort_by` | string | *results sorting parameters*<br>optional field<br>Use these parameters to sort the results by `search_volume`, `cpc`, `competition` or `relevance` in the descending order<br>default value: `relevance` |
| `date_from` | string | *starting date of the time range*<br>optional field<br>minimal value: 24 months from today’s date<br>if you don’t specify this field, data will be provided for the last 12 months<br>minimum value: two years back from today’s date<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2020-01-01"`<br>**Note:** we do not recommend using a custom time range for the past year’s dates |
| `date_to` | string | *ending date of the time range*<br>optional field<br>if you don’t specify this field, data will be provided for the last 12 months;<br>minimum value: two years back from today’s date;<br>maximum value: one month from today’s date;<br>**note:** we do not recommend using a custom time range for the past year’s dates;<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2020-03-15"`<br>**Note:** we do not recommend using a custom time range for the past year’s dates |
| `search_partners` | boolean | *Bing search partners type*<br>optional field<br>if you specify `true`, the results will be delivered for owned, operated, and syndicated networks across Bing, Yahoo, AOL and partner sites that host Bing, AOL, and Yahoo search.<br>default value: `false` – results are returned for Bing, AOL, and Yahoo search networks |
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
| `status_code` | integer | *status code of the task *<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request<br>* |
| **`result`** | array | *array of results* |
| `keyword` | string | *keyword in a POST array* |
| `location_code` | integer | *location code in a POST array*<br>if there is no data, then the value is `null` |
| `language_code` | string | *language code in a POST array*<br>if there is no data, then the value is `null` |
| `search_partners` | boolean | *indicates whether data from partner networks included in the response* |
| `device` | string | *device type in a POST array*<br>if there is no data, then the value is `null` |
| `competition` | float | *competition*<br>represents the relative amount of competition associated with the given keyword in paid SERP only. This value is based on Bing Ads data.<br>Possible values: `0.1`, `0.5`,`0.9``0.1` – low competition,<br>`0.5` – medium competition,<br>`0.9` – high competition;<br>if there is no data the value is `null` |
| `cpc` | float | *cost-per-click*<br>represents the average cost per click (USD) historically paid for the keyword.<br>if there is no data then the value is `null` |
| `search_volume` | integer | *monthly average search volume rate<br>*represents either the (approximate) number of searches for the given keyword idea on bing search engine depending on the user’s targeting;<br>search volume is rounded to the nearest tens;<br>if there is no data, the value is `null` |
| `categories` | array | *product and service categories*<br>our API doesn’t return categories for this endpoint: the parameter will always equal `null` |
| `monthly_searches` | array | *monthly searches*<br>represents the (approximate) number of searches on this keyword idea (as available for the past twelve months), targeted to the specified geographic locations<br>if there is no data then the value is `null` |
| `year` | integer | *year* |
| `month` | integer | *month* |
| `search_volume` | integer | *monthly average search volume rate*<br>search volume is rounded to the nearest tens |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Locations and Languages
*Source: [https://docs.dataforseo.com/v3/keywords_data/bing/search_volume_history/locations_and_languages/](https://docs.dataforseo.com/v3/keywords_data/bing/search_volume_history/locations_and_languages/)*
#### List of Locations and Languages for Bing ‘Search Volume History’ Endpoint

Pricing

Your account will not be charged for using this API

GEThttps://api.dataforseo.com/v3/keywords_data/bing/search_volume_history/locations_and_languages

By calling this API you will receive the list of locations and languages supported by Bing ‘Search Volume History’ endpoint.

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
| `language_name` | string | *language name* |
| `language_code` | string | *language code according to [ISO 639-1](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes)* |
| `available_locations` | array | *array of available locations for a certain language* |
| `location_code` | integer | *location code* |
| `location_name` | string | *full name of the location* |
| `country_iso_code` | string | *ISO country code of the location* |
| `location_type` | string | *location type* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Task POST
*Source: [https://docs.dataforseo.com/v3/keywords_data/bing/search_volume_history/task_post/](https://docs.dataforseo.com/v3/keywords_data/bing/search_volume_history/task_post/)*
#### Setting Bing ‘Search Volume History’ Tasks

This endpoint will provide you with historical search volume data for up to 1000 keywords in one request. You can get search volume for keywords in monthly, weekly, or daily format and specify the device type.

This is the Standard method of data retrieval. If you don’t need to receive data in real-time, this method is the best option for you. Set a task and retrieve the results when our system collects them. Execution time depends on the system workload.

If your system requires delivering instant results, [the Live method](https://docs.dataforseo.com/v3/keywords_data/bing/search_volume/live/) will be a better solution. This method doesn’t require making separate POST and GET requests to the corresponding endpoints.

Historical data is available for two previous years.

POSThttps://api.dataforseo.com/v3/keywords_data/bing/search_volume_history/task_post

Pricing

Your account will be charged only for setting a task.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/bing-ads) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). Task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute, with each POST call containing no more than 100 tasks. If your POST call contains over 100 tasks, the tasks over this limit will return the `40006` error. Visit [DataForSEO Help Center](https://dataforseo.com/help-center/best-practices-for-handling-keywords-data-api-requests) to get practical tips for request handling depending on your Keyword Data API payload volume.

You will get information for every single keyword in an array.

You can send up to 1000 keywords in one `keywords` array. Our system will charge your account per request, no matter what number of keywords an array has, the price for 1 or 1000 keywords will be the same.

You can also retrieve the results of completed tasks using the unique task identifier `id`. Alternatively, we can send them to you as soon as they are ready if you specify the `postback_url` or `pingback_url` when setting a task. Note that if your server doesn’t respond within 10 seconds, the connection will be aborted by timeout, and the task will be transferred to the [tasks_ready](https://docs.dataforseo.com/v3/keywords_data/bing/search_volume/tasks_ready/?php) list. The error code and message depend on your server’s configuration.

See [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) to learn more about using pingbacks and postbacks with DataForSEO APIs.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `keywords` | array | *keywords*<br>**required field**<br>The maximum number of keywords you can specify: 1000<br>The maximum number of characters for each keyword: 100<br>the specified keywords will be converted to lowercase, data will be provided in a separate array<br>learn more about rules and limitations of `keyword` and `keywords` fields in DataForSEO APIs in this [Help Center article](https://dataforseo.com/help-center/rules-and-limitations-of-keyword-and-keywords-fields-in-dataforseo-apis) |
| `location_name` | string | *full name of search engine location*<br>**required field if you don’t specify** `location_code` or `location_coordinate`<br>**if you use this field, you don’t need to specify `location_code` or `location_coordinate`**<br>you can receive the list of available locations of the search engine with their `location_name` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/bing/search_volume_history/locations_and_languages`<br>example:<br>`London,England,United Kingdom` |
| `location_code` | integer | *search engine location code*<br>**required field if you don’t specify** `location_name` or `location_coordinate`<br>**if you use this field, you don’t need to specify `location_name` or `location_coordinate`**<br>you can receive the list of available locations of the search engines with their `location_code` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/bing/search_volume_history/locations_and_languages`<br>example:<br>`2840` |
| `location_coordinate` | string | *GPS coordinates of a location*<br>**required field if you don’t specify** `location_name` or `location_code`<br>**if you use this field, you don’t need to specify `location_name` or `location_code`**<br>`location_coordinate` parameter should be specified in the *“latitude,longitude”* format<br>**the data will be provided for the country the specified coordinates belong to**<br>example:<br>`52.6178549,-155.352142` |
| `language_name` | string | *full name of search engine language*<br>**required field if you don’t specify** `language_code`<br>if you use this field, you don’t need to specify `language_code`<br>you can receive the list of available languages of the search engines with their `language_code` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/bing/search_volume_history/locations_and_languages`<br> |
| `language_code` | string | *search engine language code*<br>**required field if you don’t specify** `language_name`<br>if you use this field, you don’t need to specify `language_name`<br>you can receive the list of available languages of the search engines with their `language_code` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/bing/search_volume_history/locations_and_languages`<br> |
| `device` | array | *device types*<br>optional field<br>specify this field if you want to get the data for a particular device types<br>possible values: `mobile`, `desktop`, `tablet`, `non_smartphones`<br>default value: `["mobile", "desktop", "tablet", "non_smartphones"]` |
| `period` | string | *aggregates the returned data to a certain time period*<br>optional field<br>specify this field if you want to get the data in monthly, weekly or daily format<br>possible values: `monthly`, `weekly`, `daily`<br>`monthly` – returns data up to past 24 months<br>`weekly` – returns data up to past 15 weeks<br>`daily` – returns data up to past 45 days<br>default value: `monthly` |
| `date_from` | string | *starting date of the time range*<br>optional field<br>minimum value: two years back from today’s date<br>maximum value: one day from today’s date<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2020-01-01"`<br>**Note:** we do not recommend using a custom time range<br>**Note 2:** if `date_from` and `date_to` parameters are not specified, the data will be returned for the past 24 months<br>if you specify the `period` parameter:<br>with value `weekly`, you will get results for the past 15 weeks<br>with value `daily`, you will get results for the past 45 days |
| `date_to` | string | *ending date of the time range*<br>optional field<br>minimum value: two years back from today’s date;<br>maximum value: one day from today’s date;<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2020-03-15"`<br>**Note:** we do not recommend using a custom time range<br>**Note 2:** if `date_from` and `date_to` parameters are not specified, the data will be returned for the past 24 months<br>if you specify the `period` parameter:<br>with value `weekly`, you will get results for the past 15 weeks<br>with value `daily`, you will get results for the past 45 days |
| `postback_url` | string | *URL for sending task results*<br>optional field<br>once the task is completed, we will send a POST request with its results compressed in the `gzip` format to the `postback_url` you specified<br>you can use the ‘$id’ string as a `$id` variable and ‘$tag’ as urlencoded `$tag` variable. We will set the necessary values before sending the request.<br>example:<br>`http://your-server.com/postbackscript?id=$id`<br>`http://your-server.com/postbackscript?id=$id&tag=$tag`<br>**Note:** special characters in `postback_url` will be urlencoded;<br>i.a., the `#` character will be encoded into `%23`<br>learn more on our [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) |
| `pingback_url` | string | *notification URL of a completed task*<br>optional field<br>when a task is completed we will notify you by GET request sent to the URL you have specified<br>you can use the ‘$id’ string as a `$id` variable and ‘$tag’ as urlencoded `$tag` variable. We will set the necessary values before sending the request<br>example:<br>`http://your-server.com/pingscript?id=$id`<br>`http://your-server.com/pingscript?id=$id&tag=$tag`<br>**Note:** special characters in `pingback_url` will be urlencoded;<br>i.a., the `#` character will be encoded into `%23`<br>learn more on our [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) |
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
*Source: [https://docs.dataforseo.com/v3/keywords_data/bing/search_volume_history/tasks_ready/](https://docs.dataforseo.com/v3/keywords_data/bing/search_volume_history/tasks_ready/)*
#### Get Bing ‘Search Volume History’ Completed Tasks

This endpoint is designed to provide you with the list of completed tasks, which haven’t been collected yet. If you use the Standard method without specifying the `postback_url`, you can receive the list of `id` for all completed tasks using this endpoint. Then, you can collect the results using the **‘Task GET’** endpoint.

Learn more about task completion and obtaining a list of completed tasks in [this help center article.](https://dataforseo.com/help-center/completed-tasks)

**Note:** due to the peculiarities of our architecture the queue of completed tasks is updated with a small delay, which can be an issue for high-volume users. If your system requires collecting over 1000 tasks a minute, we recommend using [pingbacks/postbacks](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) instead, and applying the Tasks Ready endpoint only to obtain the IDs of failed postback tasks.

GEThttps://api.dataforseo.com/v3/keywords_data/bing/search_volume_history/tasks_ready

Pricing

Your account will not be charged when receiving results

Each separate task will remain on the list until it is collected. You can make **up to 20 API calls per minute.** With each API call, you can get 1000 tasks completed within three previous days. The list will not contain the tasks which have already been collected and the tasks that were not collected **within the three days** after completion.

Please note that if you specify the `postback_url`, the task will not be in the list of completed tasks. The task can only be found in the list if the request to your server failed, and your server returned HTTP code response less than `200` or higher than `300`.

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
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the parameters passed in the request’s URL* |
| ** `result`** | array | *array of results* |
| `id` | string | *task identifier of the completed task*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `se` | string | *search engine specified when setting the task* |
| `function` | string | *type of the task* |
| `date_posted` | string | *date when the task was posted (in the UTC format)* |
| `endpoint` | string | *URL for collecting the results of the task* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Task GET
*Source: [https://docs.dataforseo.com/v3/keywords_data/bing/search_volume_history/task_get/](https://docs.dataforseo.com/v3/keywords_data/bing/search_volume_history/task_get/)*
#### Get Bing ‘Search Volume History’ Results by id

This endpoint will provide you with historical search volume data for up to 1000 keywords in one request. You can get search volume for keywords in monthly, weekly, or daily format and specify the device type.

GEThttps://api.dataforseo.com/v3/keywords_data/bing/search_volume_history/task_get/$id

Pricing

Your account will be charged only for posting a task. You can get the results of the task within the next 30 days for free.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/bing-ads) page.

**Description of the fields for sending a request:**

| Field name | Type | Description |
| --- | --- | --- |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format**<br>you will be able to use it within **30 days** to request the results of the task at any time |

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
| `status_code` | integer | *status code of the task *<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request<br>* |
| **`result`** | array | *array of results* |
| `keyword` | string | *keyword in a POST array* |
| `location_code` | integer | *location code in a POST array*<br>if there is no data, then the value is `null` |
| `language_code` | string | *language code in a POST array*<br>if there is no data, then the value is `null` |
| `device` | string | *device type in a POST array*<br>if there is no data, then the value is `null` |
| `period` | string | *time period*<br>indicates if returned data is aggregated to a certain time period<br>default value `monthly`<br> |
| `searches` | object | *contains results distributed by device type*<br>if the `device` parameter is not specified, the data will be returned for all available device types<br> |
| `desktop` | object | *device type = **desktop***<br>contains historical search volume data for searches made from desktop devices |
| `year` | integer | *year* |
| `month` | integer | *month* |
| `day` | integer | *day of the month* |
| `search_volume` | integer | *search volume rate*<br> |
| `non_smartphones` | object | *device type = **non-smartphones***<br>contains historical search volume data for searches made from feature phones (non-smartphone mobile devices) |
| `year` | integer | *year* |
| `month` | integer | *month* |
| `day` | integer | *day of the month* |
| `search_volume` | integer | *search volume rate*<br> |
| `mobile` | object | *device type = **mobile***<br>contains historical search volume data for searches made from mobile devices |
| `year` | integer | *year* |
| `month` | integer | *month* |
| `day` | integer | *day of the month* |
| `search_volume` | integer | *search volume rate*<br> |
| `tablet` | object | *device type = **tablet***<br>contains historical search volume data for searches made from tablets |
| `year` | integer | *year* |
| `month` | integer | *month* |
| `day` | integer | *day of the month* |
| `search_volume` | integer | *search volume rate*<br> |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Live
*Source: [https://docs.dataforseo.com/v3/keywords_data/bing/search_volume_history/live/](https://docs.dataforseo.com/v3/keywords_data/bing/search_volume_history/live/)*
#### Setting Live Bing ‘Search Volume History’ Tasks

This endpoint will provide you with historical search volume data for up to 1000 keywords in one request. You can get search volume for keywords in monthly, weekly, or daily format and specify the device type.

If your system requires delivering instant results, the Live method is the best solution for you. Unlike the Standard method, this method doesn’t require making separate POST and GET requests to the corresponding endpoints.

If you don’t need to receive data in real-time, you can use the [Standard method](https://docs.dataforseo.com/v3/keywords_data/bing/search_volume/task_post/) of data retrieval. This method requires making separate POST and GET requests, but it’s more affordable. Using this method you can retrieve the results after our system collects them.

Historical data is available for 24 months.

POSThttps://api.dataforseo.com/v3/keywords_data/bing/search_volume_history/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/bing-ads) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute. Visit [DataForSEO Help Center](https://dataforseo.com/help-center/best-practices-for-handling-keywords-data-api-requests) to get practical tips for request handling depending on your Keyword Data API payload volume.

You will get information for every single keyword in an array.

You can send up to 1000 keywords in one `keywords` array. Our system will charge your account per each request, no matter what number of keywords an array has, the price for 1 or 1000 keywords will be the same.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `keywords` | array | *keywords*<br>**required field**<br>The maximum number of keywords you can specify: 1000<br>The maximum number of characters for each keyword: 100<br>the specified keywords will be converted to lowercase, data will be provided in a separate array<br>learn more about rules and limitations of `keyword` and `keywords` fields in DataForSEO APIs in this [Help Center article](https://dataforseo.com/help-center/rules-and-limitations-of-keyword-and-keywords-fields-in-dataforseo-apis) |
| `location_name` | string | *full name of search engine location*<br>**required field if you don’t specify** `location_code` or `location_coordinate`<br>**if you use this field, you don’t need to specify `location_code` or `location_coordinate`**<br>you can receive the list of available locations of the search engine with their `location_name` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/bing/search_volume_history/locations_and_languages`<br>example:<br>`London,England,United Kingdom` |
| `location_code` | integer | *search engine location code*<br>**required field if you don’t specify** `location_name` or `location_coordinate`<br>**if you use this field, you don’t need to specify `location_name` or `location_coordinate`**<br>you can receive the list of available locations of the search engines with their `location_code` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/bing/search_volume_history/locations_and_languages`<br>example:<br>`2840` |
| `location_coordinate` | string | *GPS coordinates of a location*<br>**required field if you don’t specify** `location_name` or `location_code`<br>**if you use this field, you don’t need to specify `location_name` or `location_code`**<br>`location_coordinate` parameter should be specified in the *“latitude,longitude”* format<br>**the data will be provided for the country the specified coordinates belong to**<br>example:<br>`52.6178549,-155.352142` |
| `language_name` | string | *full name of search engine language*<br>**required field if you don’t specify** `language_code`<br>if you use this field, you don’t need to specify `language_code`<br>you can receive the list of available languages of the search engines with their `language_code` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/bing/search_volume_history/locations_and_languages`<br> |
| `language_code` | string | *search engine language code*<br>**required field if you don’t specify** `language_name`<br>if you use this field, you don’t need to specify `language_name`<br>you can receive the list of available languages of the search engines with their `language_code` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/bing/search_volume_history/locations_and_languages`<br> |
| `device` | array | *device types*<br>optional field<br>specify this field if you want to get the data for a particular device types<br>possible values: `mobile`, `desktop`, `tablet`, `non_smartphones`<br>default value: `["mobile", "desktop", "tablet", "non_smartphones"]` |
| `period` | string | *aggregates the returned data to a certain time period*<br>optional field<br>specify this field if you want to get the data in monthly, weekly or daily format<br>possible values: `monthly`, `weekly`, `daily`<br>`monthly` – returns data up to past 24 months<br>`weekly` – returns data up to past 15 weeks<br>`daily` – returns data up to past 45 days<br>default value: `monthly` |
| `date_from` | string | *starting date of the time range*<br>optional field<br>minimum value: 24 months back from today’s date<br>maximum value: one day from today’s date<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2020-01-01"`<br>**Note:** we do not recommend using a custom time range<br>**Note 2:** if `date_from` and `date_to` parameters are not specified, the data will be returned for the past 24 months<br>if you specify the `period` parameter:<br>with value `weekly`, you will get results for the past 15 weeks<br>with value `daily`, you will get results for the past 45 days |
| `date_to` | string | *ending date of the time range*<br>optional field<br>minimum value: two years back from today’s date;<br>maximum value: one day from today’s date;<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2020-03-15"`<br>**Note:** we do not recommend using a custom time range<br>**Note 2:** if `date_from` and `date_to` parameters are not specified, the data will be returned for the past 24 months<br>if you specify the `period` parameter:<br>with value `weekly`, you will get results for the past 15 weeks<br>with value `daily`, you will get results for the past 45 days |
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
| `status_code` | integer | *status code of the task *<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request<br>* |
| **`result`** | array | *array of results* |
| `keyword` | string | *keyword in a POST array* |
| `location_code` | integer | *location code in a POST array*<br>if there is no data, then the value is `null` |
| `language_code` | string | *language code in a POST array*<br>if there is no data, then the value is `null` |
| `device` | string | *device type in a POST array*<br>if there is no data, then the value is `null` |
| `period` | string | *time period*<br>indicates if returned data is aggregated to a certain time period<br>default value `monthly`<br> |
| `searches` | object | *contains results distributed by device type*<br>if the `device` parameter is not specified, the data will be returned for all available device types<br> |
| `desktop` | object | *device type = **desktop***<br>contains historical search volume data for searches made from desktop devices |
| `year` | integer | *year* |
| `month` | integer | *month* |
| `day` | integer | *day of the month* |
| `search_volume` | integer | *search volume rate*<br> |
| `non_smartphones` | object | *device type = **non-smartphones***<br>contains historical search volume data for searches made from feature phones (non-smartphone mobile devices) |
| `year` | integer | *year* |
| `month` | integer | *month* |
| `day` | integer | *day of the month* |
| `search_volume` | integer | *search volume rate*<br> |
| `mobile` | object | *device type = **mobile***<br>contains historical search volume data for searches made from mobile devices |
| `year` | integer | *year* |
| `month` | integer | *month* |
| `day` | integer | *day of the month* |
| `search_volume` | integer | *search volume rate*<br> |
| `tablet` | object | *device type = **tablet***<br>contains historical search volume data for searches made from tablets |
| `year` | integer | *year* |
| `month` | integer | *month* |
| `day` | integer | *day of the month* |
| `search_volume` | integer | *search volume rate*<br> |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Task POST
*Source: [https://docs.dataforseo.com/v3/keywords_data/bing/keywords_for_site/task_post/](https://docs.dataforseo.com/v3/keywords_data/bing/keywords_for_site/task_post/)*
#### Setting ‘Keywords For Site’ Tasks

This endpoint will provide you with a list of keywords relevant to the specified website along with their search volume for the last month, search volume trend for up to 24 past months (for estimating search volume dynamics), current cost-per-click and competition level for paid search. The maximum number of returned keywords is **3000.**

This is the Standard method of data retrieval. If you don’t need to receive data in real-time, this method is the best option for you. Set a task and retrieve the results when our system collects them. Execution time depends on the system workload.

If your system requires delivering instant results, the [Live method](https://docs.dataforseo.com/v3/keywords_data/bing/keywords_for_site/live/) will be a better solution. This method doesn’t require making separate POST and GET requests to the corresponding endpoints.

Historical data is available for 24 months.

POSThttps://api.dataforseo.com/v3/keywords_data/bing/keywords_for_site/task_post

Pricing

Your account will be charged only for setting a task.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/bing-ads) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). Task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute, with each POST call containing no more than 100 tasks. If your POST call contains over 100 tasks, the tasks over this limit will return the `40006` error. Visit [DataForSEO Help Center](https://dataforseo.com/help-center/best-practices-for-handling-keywords-data-api-requests) to get practical tips for request handling depending on your Keyword Data API payload volume.

You can get up to 3000 keyword suggestions with all essential keyword data in response to one request. Your account will be charged for each request, no matter what number of keywords you receive in the result, the price for 1 or 3000 keywords will be the same.

You can also retrieve the results of completed tasks using the unique task identifier `id`. Alternatively, we can send them to you as soon as they are ready if you specify the `postback_url` or `pingback_url` when setting a task. Note that if your server doesn’t respond within 10 seconds, the connection will be aborted by timeout, and the task will be transferred to the [tasks_ready](https://docs.dataforseo.com/v3/keywords_data/bing/keywords_for_site/tasks_ready/?php) list. The error code and message depend on your server’s configuration.

See [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) to learn more about using pingbacks and postbacks with DataForSEO APIs.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `target` | string | *domain or URL*<br>**required field**<br>the URL of the webpage or the domain to scan for possible keywords |
| `location_name` | string | *full name of search engine location*<br>**required field if you don’t specify** `location_code` or `location_coordinate`<br>**if you use this field, you don’t need to specify `location_code` or `location_coordinate`**<br>you can receive the list of available locations of the search engine with their `location_name` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/bing/locations`<br>example:<br>`London,England,United Kingdom` |
| `location_code` | integer | *search engine location code*<br>**required field if you don’t specify** `location_name` or `location_coordinate`<br>**if you use this field, you don’t need to specify `location_name` or `location_coordinate`**<br>you can receive the list of available locations of the search engines with their `location_code` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/bing/locations`<br>example:<br>`2840` |
| `location_coordinate` | string | *GPS coordinates of a location*<br>**required field if you don’t specify** `location_name` or `location_code`<br>**if you use this field, you don’t need to specify `location_name` or `location_code`**<br>`location_coordinate` parameter should be specified in the *“latitude,longitude”* format<br>**the data will be provided for the country the specified coordinates belong to**<br>example:<br>`52.6178549,-155.352142` |
| `language_name` | string | *full name of search engine language*<br>**required field if you don’t specify** `language_code`<br>if you use this field, you don’t need to specify `language_code`<br>supported languages:<br>`English`, `French`, `German` |
| `language_code` | string | *search engine language code*<br>**required field if you don’t specify** `language_name`<br>if you use this field, you don’t need to specify `language_name`<br>supported languages:<br>`en`, `fr`, `de` |
| `keywords_negative` | array | *keywords negative array*<br>optional field<br>These keywords will be ignored in the results array;<br>You can specify **a maximum of 200 terms** that you want to exclude from the results;<br>the specified keywords will be converted to lowercase format |
| `device` | string | *device type*<br>optional field<br>specify this field if you want to get the data for a particular device type<br>possible values: `all`, `mobile`, `desktop`, `tablet`<br>default value: `all` |
| `sort_by` | string | *results sorting parameters*<br>optional field<br>Use these parameters to sort the results by `search_volume`, `cpc`, `competition` or `relevance` in the descending order<br>default value: `relevance` |
| `date_from` | string | *starting date of the time range*<br>optional field<br>minimal value: 24 months from today’s date;<br>if you don’t specify this field, data will be provided for the last 12 months<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2020-01-01"`<br>**Note:** we do not recommend using a custom time range for the past year’s dates |
| `date_to` | string | *ending date of the time range*<br>optional field<br>if you don’t specify this field, data will be provided for the last 12 months;<br>minimum value: two years back from today’s date;<br>maximum value: one month from today’s date;<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2020-03-15"`<br>**Note:** we do not recommend using a custom time range for the past year’s dates |
| `postback_url` | string | *URL for sending task results*<br>optional field<br>once the task is completed, we will send a POST request with its results compressed in the `gzip` format to the `postback_url` you specified<br>you can use the ‘$id’ string as a `$id` variable and ‘$tag’ as urlencoded `$tag` variable. We will set the necessary values before sending the request.<br>example:<br>`http://your-server.com/postbackscript?id=$id`<br>`http://your-server.com/postbackscript?id=$id&tag=$tag`<br>**Note:** special characters in `postback_url` will be urlencoded;<br>i.a., the `#` character will be encoded into `%23`<br>learn more on our [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) |
| `pingback_url` | string | *notification URL of a completed task*<br>optional field<br>when a task is completed we will notify you by GET request sent to the URL you have specified<br>you can use the ‘$id’ string as a `$id` variable and ‘$tag’ as urlencoded `$tag` variable. We will set the necessary values before sending the request.<br>example:<br>`http://your-server.com/pingscript?id=$id`<br>`http://your-server.com/pingscript?id=$id&tag=$tag`<br>**Note:** special characters in `pingback_url` will be urlencoded;<br>i.a., the `#` character will be encoded into `%23`<br>learn more on our [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) |
| `search_partners` | boolean | *Bing search partners type*<br>optional field<br>if you specify `true`, the results will be delivered for owned, operated, and syndicated networks across Bing, Yahoo, AOL and partner sites that host Bing, AOL, and Yahoo search.<br>default value: `false` – results are returned for Bing, AOL, and Yahoo search networks |
| `tag` | string | *user-defined task identifier*<br>optional field<br>*the character limit is 255*<br>you can use this parameter to identify the task and match it with the result<br>you will find the specified `tag` value in the `data` object of the response |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)<br>**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *general informational message* |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total *tasks* cost, USD* |
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
| `data` | object | *contains the same parameters that you specified in the POST request* |
| ** `result`** | array | *array of results*<br>in this case, the value will be `null` |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Tasks Ready
*Source: [https://docs.dataforseo.com/v3/keywords_data/bing/keywords_for_site/tasks_ready/](https://docs.dataforseo.com/v3/keywords_data/bing/keywords_for_site/tasks_ready/)*
#### Get ‘Keywords For Site’ Completed Tasks

This endpoint is designed to provide you with the list of completed tasks, which haven’t been collected yet. If you use the Standard method without specifying the `postback_url`, you can receive the list of `id` for all completed tasks using this endpoint. Then, you can collect the results using the **‘Task GET’** endpoint.

Learn more about task completion and obtaining a list of completed tasks in [this help center article.](https://dataforseo.com/help-center/completed-tasks)

**Note:** due to the peculiarities of our architecture the queue of completed tasks is updated with a small delay, which can be an issue for high-volume users. If your system requires collecting over 1000 tasks a minute, we recommend using [pingbacks/postbacks](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) instead, and applying the Tasks Ready endpoint only to obtain the IDs of failed postback tasks.

GEThttps://api.dataforseo.com/v3/keywords_data/bing/keywords_for_site/tasks_ready

Pricing

Your account will not be charged when receiving results

Each separate task will remain on the list until it is collected. You can make **up to 20 API calls per minute.** With each API call, you can get 1000 tasks completed within three previous days. The list will not contain the tasks which have already been collected and the tasks that were not collected **within the three days** after completion.

Please note that if you specify the `postback_url`, the task will not be in the list of completed tasks. The task can only be found in the list if the request to your server failed, and your server returned HTTP code response less than `200` or higher than `300`.

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
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the parameters passed in the request’s URL* |
| ** `result`** | array | *array of results* |
| `id` | string | *task identifier of the completed task*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `se` | string | *search engine specified when setting the task* |
| `function` | string | *type of the task* |
| `date_posted` | string | *date when the task was posted (in the UTC format)* |
| `endpoint` | string | *URL for collecting the results of the task* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Task GET
*Source: [https://docs.dataforseo.com/v3/keywords_data/bing/keywords_for_site/task_get/](https://docs.dataforseo.com/v3/keywords_data/bing/keywords_for_site/task_get/)*
#### Get ‘Keywords For Site’ Results by id

This endpoint will provide you with a list of keywords relevant to the specified website along with their search volume for the last month, search volume trend for the last year (for estimating search volume dynamics), current cost-per-click and competition level for paid search. The maximum number of returned keywords is **3000.**

You can get up to 3000 keyword suggestions with all essential keyword data in response to one request.

GEThttps://api.dataforseo.com/v3/keywords_data/bing/keywords_for_site/task_get/$id

Pricing

Your account will be charged only for posting a task. You can get the results of the task within the next 30 days for free.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/bing-ads) page.

**Description of the fields for sending a request:**

| Field name | Type | Description |
| --- | --- | --- |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format**<br>you will be able to use it within **30 days** to request the results of the task at any time |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)<br>**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total *tasks* cost* |
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
| `data` | object | *contains the same parameters that you specified in the POST request* |
| ** `result`** | array | *array of results* |
| `keyword` | string | *keyword in a POST array* |
| `location_code` | integer | *location code in a POST array*<br>if there is no data the value is `null` |
| `language_code` | string | *language code in a POST array*<br>if there is no data the value is `null` |
| `search_partners` | boolean | *indicates whether data from partner networks included in the response*<br> |
| `device` | string | *device type in a POST array*<br>if there is no data, then the value is `null` |
| `competition` | float | *competition*<br>represents the relative amount of competition associated with the given keyword in paid SERP only. This value is based on Bing Ads data.<br>Possible values: `0.1`, `0.5`,`0.9`<br>`0.1` – low competition,<br>`0.5` – medium competition,<br>`0.9` – high competition;<br>if there is no data the value is `null` |
| `cpc` | float | *cost-per-click*<br>represents the average cost per click (USD) historically paid for the keyword.<br>if there is no data the value is `null` |
| `search_volume` | integer | *monthly average search volume rate<br>*represents the (approximate) number of searches for the given keyword idea on Bing search engine depending on the user’s targeting<br>if there is no data then the value is `null` |
| `categories` | array | *product and service categories*<br>legacy field, the value will always be `null`<br> |
| `monthly_searches` | array | *monthly searches*<br>represents the (approximate) number of searches on this keyword idea (as available for the past twelve months), targeted to the specified geographic locations<br>search volume is rounded to the closest decimal values<br>if there is no data the value is `null` |
| `year` | integer | *year* |
| `month` | integer | *month* |
| `search_volume` | integer | *monthly average search volume rate*<br>search volume is rounded to the closest decimal values<br> |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Live
*Source: [https://docs.dataforseo.com/v3/keywords_data/bing/keywords_for_site/live/](https://docs.dataforseo.com/v3/keywords_data/bing/keywords_for_site/live/)*
#### Setting Live ‘Keywords For Site’ Tasks

This endpoint will provide you with a list of keywords relevant to the specified URL along with their search volume for the last month, search volume trend for up to 24 past months (for estimating search volume dynamics), current cost-per-click and competition values for paid search. The maximum number of returned keywords is **3000.**

If your system requires delivering instant results, the Live method is the best solution for you. Unlike the Standard method, this method doesn’t require making separate POST and GET requests to the corresponding endpoints.

If you don’t need to receive data in real-time, you can use [the Standard method](https://docs.dataforseo.com/v3/keywords_data/bing/keywords_for_site/task_post/) of data retrieval. This method requires making separate POST and GET requests, but it’s more affordable. Using this method you can retrieve the results after our system collects them.

Historical data is available for 24 months.

POSThttps://api.dataforseo.com/v3/keywords_data/bing/keywords_for_site/live

Pricing

Your account is charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/bing-ads) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute. Visit [DataForSEO Help Center](https://dataforseo.com/help-center/best-practices-for-handling-keywords-data-api-requests) to get practical tips for request handling depending on your Keyword Data API payload volume.

You can get up to 3000 keyword suggestions with all essential keyword data in response to one request. Your account will be charged for each request, no matter what number of keywords you receive in the result, the price for 1 or 3000 keywords will be the same.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `target` | string | *domain or URL*<br>**required field**<br>the domain name or URL of the target website |
| `location_name` | string | *full name of search engine location*<br>**required field if you don’t specify** `location_code` or `location_coordinate`<br>**if you use this field, you don’t need to specify `location_code` or `location_coordinate`**<br>you can receive the list of available locations of the search engine with their `location_name` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/bing/locations`<br>example:<br>`London,England,United Kingdom` |
| `location_code` | integer | *search engine location code*<br>**required field if you don’t specify** `location_name` or `location_coordinate`<br>**if you use this field, you don’t need to specify `location_name` or `location_coordinate`**<br>you can receive the list of available locations of the search engines with their `location_code` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/bing/locations`<br>example:<br>`2840` |
| `location_coordinate` | string | *GPS coordinates of a location*<br>**required field if you don’t specify** `location_name` or `location_code`<br>**if you use this field, you don’t need to specify `location_name` or `location_code`**<br>`location_coordinate` parameter should be specified in the *“latitude,longitude”* format<br>**the data will be provided for the country the specified coordinates belong to**<br>example:<br>`52.6178549,-155.352142` |
| `language_name` | string | *full name of search engine language*<br>**required field if you don’t specify** `language_code`<br>if you use this field, you don’t need to specify `language_code`<br>supported languages:<br>`English`, `French`, `German` |
| `language_code` | string | *search engine language code*<br>**required field if you don’t specify** `language_name`<br>if you use this field, you don’t need to specify `language_name`<br>supported languages:<br>`en`, `fr`, `de` |
| `keywords_negative` | array | *keywords negative array*<br>optional field<br>These keywords will be ignored in the results array;<br>You can specify **a maximum of 200 terms** that you want to exclude from the results;<br>the specified keywords will be converted to lowercase format |
| `device` | string | *device type*<br>optional field<br>specify this field if you want to get the data for a particular device typepossible values: `all`, `mobile`, `desktop`, `tablet`<br>default value: `all` |
| `date_from` | string | *starting date of the time range*<br>optional field<br>minimal value: 24 months from today’s date;<br>if you don’t specify this field, data will be provided for the last 12 months<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2020-01-01"`<br>**Note:** we do not recommend using a custom time range for the past year’s dates |
| `date_to` | string | *ending date of the time range*<br>optional field<br>if you don’t specify this field, data will be provided for the last 12 months;<br>minimum value: two years back from today’s date;<br>maximum value: one month from today’s date;<br>**note:** we do not recommend using a custom time range for the past year’s dates;<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2020-03-15"`<br>**Note:** we do not recommend using a custom time range for the past year’s dates |
| `sort_by` | string | *results sorting parameters*<br>optional field<br>Use these parameters to sort the results by `search_volume`, `cpc`, `competition` or `relevance` in the descending order<br>default value: `relevance` |
| `search_partners` | boolean | *Bing search partners type*<br>optional field<br>if you specify `true`, the results will be delivered for owned, operated, and syndicated networks across Bing, Yahoo, AOL and partner sites that host Bing, AOL, and Yahoo search.<br>default value: `false` – results are returned for Bing, AOL, and Yahoo search networks |
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
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array that were returned an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| ** `result`** | array | *array of results* |
| `keyword` | string | *keyword in a POST array* |
| `location_code` | integer | *location code in a POST array* |
| `language_code` | string | *language code in a POST array* |
| `search_partners` | boolean | *indicates whether data from partner networks included in the response* |
| `device` | string | *device type in a POST array*<br>if there is no data, then the value is `null` |
| `competition` | float | *competition*<br>represents the relative amount of competition associated with the given keyword in paid SERP only. This value is based on Bing Ads data.<br>Possible values: `0.1`, `0.5`,`0.9``0.1` – low competition,<br>`0.5` – medium competition,<br>`0.9` – high competition;<br>if there is no data the value is `null` |
| `cpc` | float | *cost-per-click*<br>represents the average cost per click (USD) historically paid for the keyword.<br>if there is no data, then the value is `null` |
| `search_volume` | integer | *monthly average search volume rate<br>*represents the (approximate) number of searches for the keyword on the Bing search engine, depending on the user’s targetingsearch volume is rounded to the closest decimal valuesif there is no data, then the value is `null` |
| `categories` | array | *product and service categories*<br>legacy field, the value will always be `null` |
| `monthly_searches` | array | *monthly searches*<br>represents the (approximate) number of searches on this keyword (as available for the past twelve months), targeted to the specified geographic locations.<br>if there is no data, then the value is `null` |
| `year` | integer | *year* |
| `month` | integer | *month* |
| `search_volume` | integer | *monthly average search volume rate*<br>search volume is rounded to the closest decimal values |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Task POST
*Source: [https://docs.dataforseo.com/v3/keywords_data/bing/keywords_for_keywords/task_post/](https://docs.dataforseo.com/v3/keywords_data/bing/keywords_for_keywords/task_post/)*
#### Setting ‘Keywords For Keywords’ Tasks

This endpoint will select relevant keywords for the specified terms. Set up to 200 keywords and get the results, which are suggested by Bing Ads for your query. You can get up to 3000 keyword suggestions using this function.

This is the Standard method of data retrieval. If you don’t need to receive data in real-time, this method is the best option for you. Set a task and retrieve the results when our system collects them. Execution time depends on the system workload.

If your system requires delivering instant results, [the Live method](https://docs.dataforseo.com/v3/keywords_data/bing/keywords_for_keywords/live/) will be a better solution. This method doesn’t require making separate POST and GET requests to the corresponding endpoints.

Historical data is available for 24 months.

POSThttps://api.dataforseo.com/v3/keywords_data/bing/keywords_for_keywords/task_post

Pricing

Your account will be charged only for setting a task.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/bing-ads) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). Task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute, with each POST call containing no more than 100 tasks. If your POST call contains over 100 tasks, the tasks over this limit will return the `40006` error. Visit [DataForSEO Help Center](https://dataforseo.com/help-center/best-practices-for-handling-keywords-data-api-requests) to get practical tips for request handling depending on your Keyword Data API payload volume.

You can also retrieve the results of completed tasks using the unique task identifier `id`. Alternatively, we can send them to you as soon as they are ready if you specify the `postback_url` or `pingback_url` when setting a task. Note that if your server doesn’t respond within 10 seconds, the connection will be aborted by timeout, and the task will be transferred to the [tasks_ready](https://docs.dataforseo.com/v3/keywords_data/bing/keywords_for_keywords/tasks_ready/?php) list. The error code and message depend on your server’s configuration.

See [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) to learn more about using pingbacks and postbacks with DataForSEO APIs.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `keywords` | array | *keywords*<br>**required field**<br>you can specify **the maximum of 200 keywords** with each keyword containing no more than **100 characters**;<br>the specified keywords will be converted to lowercase, data will be provided in a separate array<br>learn more about rules and limitations of `keyword` and `keywords` fields in DataForSEO APIs in this [Help Center article](https://dataforseo.com/help-center/rules-and-limitations-of-keyword-and-keywords-fields-in-dataforseo-apis) |
| `location_name` | string | *full name of search engine location*<br>**required field if you don’t specify** `location_code` or `location_coordinate`<br>**if you use this field, you don’t need to specify `location_code` or `location_coordinate`**<br>you can receive the list of available locations of the search engine with their `location_name` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/bing/locations`<br>example:<br>`London,England,United Kingdom` |
| `location_code` | integer | *search engine location code*<br>**required field if you don’t specify** `location_name` or `location_coordinate`<br>**if you use this field, you don’t need to specify `location_name` or `location_coordinate`**<br>you can receive the list of available locations of the search engines with their `location_code` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/bing/locations`<br>example:<br>`2840` |
| `location_coordinate` | string | *GPS coordinates of a location*<br>**required field if you don’t specify** `location_name` or `location_code`<br>**if you use this field, you don’t need to specify `location_name` or `location_code`**<br>`location_coordinate` parameter should be specified in the *“latitude,longitude”* format<br>**the data will be provided for the country the specified coordinates belong to**<br>example:<br>`52.6178549,-155.352142` |
| `language_name` | string | *full name of search engine language*<br>**required field if you don’t specify** `language_code`<br>if you use this field, you don’t need to specify `language_code`<br>supported languages:<br>`English`, `French`, `German` |
| `language_code` | string | *search engine language code*<br>**required field if you don’t specify** `language_name`<br>if you use this field, you don’t need to specify `language_name`<br>supported languages:<br>`en`, `fr`, `de` |
| `sort_by` | string | *results sorting parameters*<br>optional field<br>Use these parameters to sort the results by `search_volume`, `cpc`, `competition` or `relevance` in the descending order<br>default value: `relevance` |
| `keywords_negative` | array | *keywords negative array*<br>optional field<br>These keywords will be ignored in the results array;<br>You can specify **a maximum of 200 terms** that you want to exclude from the results;<br>the specified keywords will be converted to lowercase format |
| `device` | string | *device type*<br>optional field<br>specify this field if you want to get the data for a particular device type;<br>possible values: `all`, `mobile`, `desktop`, `tablet`<br>default value: `all` |
| `date_from` | string | *starting date of the time range*<br>optional field<br>minimal value: 24 months from today’s date;<br>if you don’t specify this field, data will be provided for the last 12 months<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2020-01-01"`<br>**Note:** we do not recommend using a custom time range for the past year’s dates |
| `date_to` | string | *ending date of the time range*<br>optional field<br>if you don’t specify this field, data will be provided for the last 12 months;<br>minimum value: two years back from today’s date;<br>maximum value: one month from today’s date;<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2020-03-15"`<br>**Note:** we do not recommend using a custom time range for the past year’s dates |
| `search_partners` | boolean | *Bing search partners type*<br>optional field<br>if you specify `true`, the results will be delivered for owned, operated, and syndicated networks across Bing, Yahoo, AOL and partner sites that host Bing, AOL, and Yahoo search.<br>default value: `false` – results are returned for Bing, AOL, and Yahoo search networks |
| `postback_url` | string | *URL for sending task results*<br>optional field<br>once the task is completed, we will send a POST request with its results compressed in the `gzip` format to the `postback_url` you specified<br>you can use the ‘$id’ string as a `$id` variable and ‘$tag’ as urlencoded `$tag` variable. We will set the necessary values before sending the request.<br>example:<br>`http://your-server.com/postbackscript?id=$id`<br>`http://your-server.com/postbackscript?id=$id&tag=$tag`<br>**Note:** special characters in `postback_url` will be urlencoded;<br>i.a., the `#` character will be encoded into `%23`<br>learn more on our [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) |
| `pingback_url` | string | *notification URL of a completed task*<br>optional field<br>when a task is completed we will notify you by GET request sent to the URL you have specified<br>you can use the ‘$id’ string as a `$id` variable and ‘$tag’ as urlencoded `$tag` variable. We will set the necessary values before sending the request.<br>example:<br>`http://your-server.com/pingscript?id=$id`<br>`http://your-server.com/pingscript?id=$id&tag=$tag`<br>**Note:** special characters in `pingback_url` will be urlencoded;<br>i.a., the `#` character will be encoded into `%23`<br>learn more on our [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) |
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
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
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
*Source: [https://docs.dataforseo.com/v3/keywords_data/bing/keywords_for_keywords/tasks_ready/](https://docs.dataforseo.com/v3/keywords_data/bing/keywords_for_keywords/tasks_ready/)*
#### Get ‘Keywords For Keywords’ Completed Tasks

This endpoint is designed to provide you with the list of completed tasks, which haven’t been collected yet. If you use the Standard method without specifying the `postback_url`, you can receive the list of `id` for all completed tasks using this endpoint. Then, you can collect the results using the **‘Task GET’** endpoint.

Learn more about task completion and obtaining a list of completed tasks in [this help center article.](https://dataforseo.com/help-center/completed-tasks)

**Note:** due to the peculiarities of our architecture the queue of completed tasks is updated with a small delay, which can be an issue for high-volume users. If your system requires collecting over 1000 tasks a minute, we recommend using [pingbacks/postbacks](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) instead, and applying the Tasks Ready endpoint only to obtain the IDs of failed postback tasks.

GEThttps://api.dataforseo.com/v3/keywords_data/bing/keywords_for_keywords/tasks_ready

Pricing

Your account will not be charged when receiving results

Each separate task will remain on the list until it is collected. You can make **up to 20 API calls per minute.** With each API call, you can get 1000 tasks completed within three previous days. The list will not contain the tasks which have already been collected and the tasks that were not collected **within the three days** after completion.

Please note that if you specify the `postback_url`, the task will not be in the list of completed tasks. The task can only be found in the list if the request to your server failed, and your server returned HTTP code response less than `200` or higher than `300`.

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
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the parameters passed in the request’s URL* |
| ** `result`** | array | *array of results* |
| `id` | string | *task identifier of the completed task*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `se` | string | *search engine specified when setting the task* |
| `function` | string | *type of the task* |
| `date_posted` | string | *date when the task was posted (in the UTC format)* |
| `endpoint` | string | *URL for collecting the results of the task* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Task GET
*Source: [https://docs.dataforseo.com/v3/keywords_data/bing/keywords_for_keywords/task_get/](https://docs.dataforseo.com/v3/keywords_data/bing/keywords_for_keywords/task_get/)*
#### Get ‘Keywords For Keywords’ Results by id

This endpoint will select relevant keywords for the specified terms. Set up to 200 keywords and get the results, which are suggested by Bing Ads for your query. You can get up to 3000 keyword suggestions using this function.

GEThttps://api.dataforseo.com/v3/keywords_data/bing/keywords_for_keywords/task_get/$id

Pricing

Your account will be charged only for posting a task. You can get the results of the task within the next 30 days for free.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/bing-ads) page.

**Description of the fields for sending a request:**

| Field name | Type | Description |
| --- | --- | --- |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format**<br>you will be able to use it within **30 days** to request the results of the task at any time |

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
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| ** `result`** | array | *array of results* |
| `keyword` | string | *keyword in a POST array* |
| `location_code` | integer | *location code in a POST array*<br> |
| `language_code` | string | *language code in a POST array*<br> |
| `search_partners` | boolean | *indicates whether data from partner networks included in the response*<br> |
| `device` | string | *device type*<br>indicates for what device type the data is provided;<br>possible values: `all`, `mobile`, `desktop`, `tablet` |
| `competition` | float | *competition*<br>represents the relative amount of competition associated with the given keyword in paid SERP only. This value is based on Bing Ads data.<br>Possible values: `0.1`, `0.5`,`0.9`<br>`0.1` – low competition,<br>`0.5` – medium competition,<br>`0.9` – high competition;<br>if there is no data the value is `null` |
| `cpc` | float | *cost-per-click*<br>represents the average cost per click (USD) historically paid for the keyword.<br>if there is no data, then the value is `null` |
| `search_volume` | integer | *monthly average search volume rate*<br>represents the (approximate) number of searches for the keyword on the Bing search engine, depending on the user’s targeting<br>search volume is rounded to the closest decimal values<br>if there is no data, then the value is `null` |
| `categories` | array | *product and service categories*<br>legacy field, the value will always be `null`<br> |
| `monthly_searches` | array | *monthly searches*<br>represents the (approximate) number of searches on this keyword (as available for the past twelve months), targeted to the specified geographic locations.<br>if there is no data, then the value is `null` |
| `year` | integer | *year* |
| `month` | integer | *month* |
| `search_volume` | integer | *monthly average search volume rate*<br>search volume is rounded to the closest decimal values |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Live
*Source: [https://docs.dataforseo.com/v3/keywords_data/bing/keywords_for_keywords/live/](https://docs.dataforseo.com/v3/keywords_data/bing/keywords_for_keywords/live/)*
#### Setting Live ‘Keywords For Keywords’ Tasks

This endpoint will select the relevant keywords for the specified ones. Set up to 200 keywords and get the results, which are suggested by Bing Ads for your query. You can get up to 3000 keyword suggestions using this function.

If your system requires delivering instant results, the Live method is the best solution for you. Unlike [the Standard method](https://docs.dataforseo.com/v3/keywords_data/bing/keywords_for_keywords/task_post/), this method doesn’t require making separate POST and GET requests to the corresponding endpoints.

If you don’t need to receive data in real-time, you can use the Standard method of data retrieval. This method requires making separate POST and GET requests, but it’s more affordable. Using this method you can retrieve the results after our system collects them.

Historical data is available for 24 months.

POSThttps://api.dataforseo.com/v3/keywords_data/bing/keywords_for_keywords/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/bing-ads) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute. Visit [DataForSEO Help Center](https://dataforseo.com/help-center/best-practices-for-handling-keywords-data-api-requests) to get practical tips for request handling depending on your Keyword Data API payload volume.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `keywords` | array | *keywords*<br>**required field**<br>you can specify **the maximum of 200 keywords** with each keyword containing no more than **100 characters**;<br>the specified keywords will be converted to lowercase, data will be provided in a separate array<br>learn more about rules and limitations of `keyword` and `keywords` fields in DataForSEO APIs in this [Help Center article](https://dataforseo.com/help-center/rules-and-limitations-of-keyword-and-keywords-fields-in-dataforseo-apis) |
| `location_name` | string | *full name of search engine location*<br>**required field if you don’t specify** `location_code` or `location_coordinate`<br>**if you use this field, you don’t need to specify `location_code` or `location_coordinate`**<br>you can receive the list of available locations of the search engine with their `location_name` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/bing/locations`<br>example:<br>`London,England,United Kingdom` |
| `location_code` | integer | *search engine location code*<br>**required field if you don’t specify** `location_name` or `location_coordinate`<br>**if you use this field, you don’t need to specify `location_name` or `location_coordinate`**<br>you can receive the list of available locations of the search engines with their `location_code` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/bing/locations`<br>example:<br>`2840` |
| `location_coordinate` | string | *GPS coordinates of a location*<br>**required field if you don’t specify** `location_name` or `location_code`<br>**if you use this field, you don’t need to specify `location_name` or `location_code`**<br>`location_coordinate` parameter should be specified in the *“latitude,longitude”* format<br>**the data will be provided for the country the specified coordinates belong to**<br>example:<br>`52.6178549,-155.352142` |
| `language_name` | string | *full name of search engine language*<br>**required field if you don’t specify** `language_code`<br>if you use this field, you don’t need to specify `language_code`<br>supported languages:<br>`English`, `French`, `German` |
| `language_code` | string | *search engine language code*<br>**required field if you don’t specify** `language_name`<br>if you use this field, you don’t need to specify `language_name`<br>supported languages:<br>`en`, `fr`, `de` |
| `sort_by` | string | *results sorting parameters*<br>optional field<br>Use these parameters to sort the results by `search_volume`, `cpc`, `competition` or `relevance` in the descending order<br>default value: `relevance` |
| `keywords_negative` | array | *keywords negative array*<br>optional field<br>These keywords will be ignored in the results array;<br>You can specify **a maximum of 200 terms** that you want to exclude from the results;<br>the specified keywords will be converted to lowercase format |
| `device` | string | *device type*<br>optional field<br>specify this field if you want to get the data for a particular device type;<br>possible values: `all`, `mobile`, `desktop`, `tablet`<br>default value: `all` |
| `date_from` | string | *starting date of the time range*<br>optional field<br>minimal value: 24 months from today’s date;<br>if you don’t specify this field, data will be provided for the last 12 months<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2020-01-01"`<br>**Note:** we do not recommend using a custom time range for the past year’s dates |
| `date_to` | string | *ending date of the time range*<br>optional field<br>if you don’t specify this field, data will be provided for the last 12 months;<br>minimum value: two years back from today’s date;<br>maximum value: one month from today’s date;<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2020-03-15"`<br>**Note:** we do not recommend using a custom time range for the past year’s dates |
| `search_partners` | boolean | *Bing search partners type*<br>optional field<br>if you specify `true`, the results will be delivered for owned, operated, and syndicated networks across Bing, Yahoo, AOL and partner sites that host Bing, AOL, and Yahoo search.<br>default value: `false` – results are returned for Bing, AOL, and Yahoo search networks |
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
| `tasks_error` | integer | *the number of tasks in the **`tasks` array** returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| ** `result`** | array | *array of results* |
| `keyword` | string | *keyword in a POST array* |
| `location_code` | integer | *location code in a POST array*<br>if there is no data, then the value is `null` |
| `language_code` | string | *language code in a POST array*<br>if there is no data, then the value is `null` |
| `search_partners` | boolean | *indicates whether data from partner networks is included in the response* |
| `device` | string | *device type*<br>indicates for what device type the data is provided;<br>possible values: `all`, `mobile`, `desktop`, `tablet` |
| `competition` | float | *competition*<br>represents the relative amount of competition associated with the given keyword in paid SERP only. This value is based on Bing Ads data.<br>Possible values: `0.1`, `0.5`,`0.9``0.1` – low competition,<br>`0.5` – medium competition,<br>`0.9` – high competition;<br>if there is no data the value is `null` |
| `cpc` | float | *cost-per-click*<br>represents the average cost per click (USD) historically paid for the keyword.<br>if there is no data, then the value is `null` |
| `search_volume` | integer | *monthly average search volume rate*<br>represents the (approximate) number of searches for the keyword on the Bing search engine, depending on the user’s targetingsearch volume is rounded to the closest decimal values<br>if there is no data, then the value is `null` |
| `categories` | array | *product and service categories*<br>legacy field, the value will always be `null` |
| `monthly_searches` | array | *monthly searches*<br>represents the (approximate) number of searches on this keyword (as available for the past twelve months), targeted to the specified geographic locations.<br>if there is no data, then the value is `null` |
| `year` | integer | *year* |
| `month` | integer | *month* |
| `search_volume` | integer | *monthly average search volume rate*<br>search volume is rounded to the closest decimal values |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Locations and Languages
*Source: [https://docs.dataforseo.com/v3/keywords_data/bing/keyword_performance/locations_and_languages/](https://docs.dataforseo.com/v3/keywords_data/bing/keyword_performance/locations_and_languages/)*
#### List of Locations and Languages for Keyword Performance endpoints

Using this endpoint you can get the full list of locations and languages supported in Keyword Performance endpoints of Bing Keywords Data API.

GEThttps://api.dataforseo.com/v3/keywords_data/bing/keyword_performance/locations_and_languages

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
| `language_name` | integer | *language name* |
| `language_code` | string | *language code* |
| `available_locations` | array | *supported locations*<br>contains locations supported in combination with a specific language |
| `location_code` | string | *location code* |
| `location_name` | string | *location name* |
| `country_iso_code` | string | *ISO country code of the location* |
| `location_type` | string | *location type*<br>possible values:<br>`Country`, `Region` |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Task POST
*Source: [https://docs.dataforseo.com/v3/keywords_data/bing/keyword_performance/task_post/](https://docs.dataforseo.com/v3/keywords_data/bing/keyword_performance/task_post/)*
#### Setting ‘Bing Keyword Performance’ Tasks

You can receive a set of keyword performance stats for a group of keywords depending on the specified match type, location and language parameters. Ad position, clicks, impressions, and other keyword metrics are aggregated for the last month for one or all of the following device types: mobile, desktop, tablet.

Generally, Bing provides the updated data after the 3rd day of a month. For example, if you request keyword data on August 1st, 2nd, or 3rd, and data for July is not available yet, you will receive the data for June. After the 4th day of a month when the update is completed by Bing, the `month` field in the `result` array will indicate that data is already provided for the previous calendar month.

You will get information separately for each keyword specified in a POST array.

This is the Standard method of data retrieval. If you don’t need to receive data in real-time, this method is the best option for you. Set a task and retrieve the results when our system collects them. Execution time depends on the system workload.

If your system requires delivering instant results, [the Live method](https://docs.dataforseo.com/v3/keywords_data/bing/keyword_performance/live) will be a better solution. This method doesn’t require making separate POST and GET requests to the corresponding endpoints.

POSThttps://api.dataforseo.com/v3/keywords_data/bing/keyword_performance/task_post

Pricing

Your account will be charged only for setting a task.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/bing-ads) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). Task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute, with each POST call containing no more than 100 tasks. If your POST call contains over 100 tasks, the tasks over this limit will return the `40006` error. Visit [DataForSEO Help Center](https://dataforseo.com/help-center/best-practices-for-handling-keywords-data-api-requests) to get practical tips for request handling depending on your Keyword Data API payload volume.

You can send up to 1000 keywords in one `keywords` array. Our system will charge your account per request, no matter what number of keywords an array has, the price for 1 or 1000 keywords will be the same.

You can also retrieve the results of completed tasks using the unique task identifier `id`. Alternatively, we can send them to you as soon as they are ready if you specify the `postback_url` or `pingback_url` when setting a task. Note that if your server doesn’t respond within 10 seconds, the connection will be aborted by timeout, and the task will be transferred to the [tasks_ready](https://docs.dataforseo.com/v3/keywords_data/bing/keyword_performance/tasks_ready/?php) list. The error code and message depend on your server’s configuration.

See [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) to learn more about using pingbacks and postbacks with DataForSEO APIs.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `keywords` | array | *keywords*<br>**required field**<br>The maximum number of keywords you can specify: 1000<br>The maximum number of characters for each keyword: 80<br>The maximum number of words for each keyword phrase: 10<br>the specified keywords will be converted to lowercase, data will be provided in a separate array<br>learn more about rules and limitations of `keyword` and `keywords` fields in DataForSEO APIs in this [Help Center article](https://dataforseo.com/help-center/rules-and-limitations-of-keyword-and-keywords-fields-in-dataforseo-apis) |
| `device` | string | *device type*<br>optional field<br>specify this field if you want to get the data for a particular device typepossible values: `desktop`, `mobile`, `tablet`, `all`<br>default value: `all` |
| `match` | string | *keywords match type*<br>optional field<br>can take the following values:<br>`aggregate` returns data across all match types;<br>`broad` returns data for all user queries containing the specified keyword with varying word order;<br>`phrase` returns data for all user queries containing the specified keyword with identical word order;<br>`exact` returns data for user query that matches the specified keyword;**Note:** the `aggregate` match type is applied by default |
| `location_name` | string | *full name of search engine location*<br>**required field if you don’t specify** `location_code` or `location_coordinate`<br>**if you use this field, you don’t need to specify `location_code` or `location_coordinate`**<br>you can receive the list of available locations and languages by making a separate request to `https://api.dataforseo.com/v3/keywords_data/bing/keyword_performance/locations_and_languages`<br>example:<br>`"United States"` |
| `location_code` | integer | *search engine location code*<br>**required field if you don’t specify** `location_name` or `location_coordinate`<br>**if you use this field, you don’t need to specify `location_name` or `location_coordinate`**<br>you can receive the list of available locations and languages by making a separate request to `https://api.dataforseo.com/v3/keywords_data/bing/keyword_performance/locations_and_languages`<br>example:<br>`2840` |
| `location_coordinate` | string | *GPS coordinates of a location*<br>**required field if you don’t specify** `location_name` or `location_code`<br>**if you use this field, you don’t need to specify `location_name` or `location_code`**<br>`location_coordinate` parameter should be specified in the *“latitude,longitude”* format<br>**the data will be provided for the country the specified coordinates belong to**<br>example:<br>`52.6178549,-155.352142` |
| `language_name` | string | *full name of search engine language*<br>**required field if you don’t specify** `language_code`<br>**if you use this field, you don’t need to specify `language_code`**<br>you can receive the list of available locations and languages by making a separate request to `https://api.dataforseo.com/v3/keywords_data/bing/keyword_performance/locations_and_languages`<br>example:<br>`English` |
| `language_code` | string | *search engine language code*<br>**required field if you don’t specify** `language_name`<br>you can receive the list of available locations and languages by making a separate request to `https://api.dataforseo.com/v3/keywords_data/bing/keyword_performance/locations_and_languages`<br>example:<br>`"en"` |
| `postback_url` | string | *URL for sending task results*<br>optional field<br>once the task is completed, we will send a POST request with its results compressed in the `gzip` format to the `postback_url` you specified<br>you can use the ‘$id’ string as a `$id` variable and ‘$tag’ as urlencoded `$tag` variable. We will set the necessary values before sending the request.<br>example:<br>`http://your-server.com/postbackscript?id=$id`<br>`http://your-server.com/postbackscript?id=$id&tag=$tag`<br>**Note:** special characters in `postback_url` will be urlencoded;<br>i.a., the `#` character will be encoded into `%23`<br>learn more on our [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) |
| `pingback_url` | string | *notification URL of a completed task*<br>optional field<br>when a task is completed we will notify you by GET request sent to the URL you have specified<br>you can use the ‘$id’ string as a `$id` variable and ‘$tag’ as urlencoded `$tag` variable. We will set the necessary values before sending the request<br>example:<br>`http://your-server.com/pingscript?id=$id`<br>`http://your-server.com/pingscript?id=$id&tag=$tag`<br>**Note:** special characters in `pingback_url` will be urlencoded;<br>i.a., the `#` character will be encoded into `%23`<br>learn more on our [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) |
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
| `tasks_count` | integer | *the number of tasks in the **`tasks`**array* |
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array returned with an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *unique task identifier in our system*<br>in the [Universally unique identifier (UUID)](https://en.wikipedia.org/wiki/Universally_unique_identifier) format |
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
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
*Source: [https://docs.dataforseo.com/v3/keywords_data/bing/keyword_performance/tasks_ready/](https://docs.dataforseo.com/v3/keywords_data/bing/keyword_performance/tasks_ready/)*
#### Get ‘Keyword Performance’ Completed Tasks

This endpoint is designed to provide you with the list of completed tasks, which haven’t been collected yet. If you use the Standard method without specifying the `postback_url`, you can receive the list of `id` for all completed tasks using this endpoint. Then, you can collect the results using the **‘Task GET’** endpoint.

Learn more about task completion and obtaining a list of completed tasks in [this help center article.](https://dataforseo.com/help-center/completed-tasks)

**Note:** due to the peculiarities of our architecture the queue of completed tasks is updated with a small delay, which can be an issue for high-volume users. If your system requires collecting over 1000 tasks a minute, we recommend using [pingbacks/postbacks](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) instead, and applying the Tasks Ready endpoint only to obtain the IDs of failed postback tasks.

GEThttps://api.dataforseo.com/v3/keywords_data/bing/keyword_performance/tasks_ready

Pricing

Your account will not be charged when receiving results

Each separate task will remain on the list until it is collected. You can make **up to 20 API calls per minute.** With each API call, you can get 1000 tasks completed within three previous days. The list will not contain the tasks which have already been collected and the tasks that were not collected **within the three days** after completion.

Please note that if you specify the `postback_url`, the task will not be in the list of completed tasks. The task can only be found in the list if the request to your server failed, and your server returned HTTP code response less than `200` or higher than `300`.

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
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the parameters passed in the request’s URL* |
| ** `result`** | array | *array of results* |
| `id` | string | *task identifier of the completed task*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `se` | string | *search engine specified when setting the task* |
| `function` | string | *type of the task* |
| `date_posted` | string | *date when the task was posted (in the UTC format)* |
| `endpoint` | string | *URL for collecting the results of the task* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Task GET
*Source: [https://docs.dataforseo.com/v3/keywords_data/bing/keyword_performance/task_get/](https://docs.dataforseo.com/v3/keywords_data/bing/keyword_performance/task_get/)*
#### Get ‘Bing Keyword Performance’ Results by id

You can receive a set of keyword performance stats for a group of keywords depending on the specified match type, location and language parameters. Ad position, clicks, impressions, and other keyword metrics are aggregated for the last month for one or all of the following device types: mobile, desktop, tablet.

You will get information separately for each keyword specified in a POST array.

GEThttps://api.dataforseo.com/v3/keywords_data/bing/keyword_performance/task_get/$id

Pricing

Your account will be charged only for posting a task. You can get the results of the task within the next 30 days for free.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/bing-ads) page.

**Description of the fields for sending a request:**

| Field name | Type | Description |
| --- | --- | --- |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format**<br>you will be able to use it within **30 days** to request the results of the task at any time |

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
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `keyword` | string | *keyword in a POST array* |
| `location_code` | integer | *location code in a POST array*<br>if there is no data, then the value is `null` |
| `language_code` | string | *language code in a POST array*<br>if there is no data, then the value is `null` |
| `year` | integer | *indicates the year for which the data is provided for*<br>example:<br>`2020`<br> `month`<br>integer<br>*indicates the month for which the data is provided for*<br>example:<br>`10`<br> `keyword_kpi`<br>object<br>*object containing keyword metrics*<br>if there is no data, then the value is `null`<br> **`desktop`**<br>array<br>*keyword data aggregated for desktop devices*<br>if there is no data, then the value is `null`<br> `ad_position`<br>string<br>*represents the position of the relevant ad in SERP*<br>can take the following values:<br>`FirstPage1`: The first ad to appear on the right side of the first search results page<br>`FirstPage2`: The second ad to appear on the right side of the first search results page<br>`FirstPage3`: The third ad to appear on the right side of the first search results page<br>`FirstPage4`: The fourth ad to appear on the right side of the first search results page<br>`FirstPage5`: The fifth ad to appear on the right side of the first search results page<br>`FirstPage6`: The sixth ad to appear on the right side of the first search results page<br>`FirstPage7`: The seventh ad to appear on the right side of the first search results page<br>`FirstPage8`: The eighth ad to appear on the right side of the first search results page<br>`FirstPage9`: The ninth ad to appear on the right side of the first search results page<br>`FirstPage10`: The tenth ad to appear on the right side of the first search results page<br>`MainLine1`: The first ad to appear at the top of the search results page<br>`MainLine2`: The second ad to appear at the top of the search results page<br>`MainLine3`: The third ad to appear at the top of the search results page<br>`MainLine4`: The fourth ad to appear at the top of the search results page<br> `clicks`<br>integer<br>*ad clicks*<br>the number of clicks that the keyword and match type generated during the last month<br> `impressions`<br>integer<br>*ad impressions*<br>the number of impressions that the keyword and match type generated during the last month<br> `average_cpc`<br>integer<br>*average cost per click, USD*<br>calculated by dividing the cost of all clicks by the number of clicks<br> `ctr`<br>integer<br>*click-through rate as a percentage*<br>calculated by dividing the number of clicks by the number of impressions and multiplying the result by 100<br> `total_cost`<br>integer<br>*total cost of an ad, USD*<br>the cost of using the specified keyword and match type during the last month<br> `average_bid`<br>integer<br>*average bid of the keyword*<br> **`mobile`**<br>array<br>*keyword data aggregated for mobile devices*<br>if there is no data, then the value is `null`<br> `ad_position`<br>string<br>*represents the position of the relevant ad in SERP*<br>can take the following values:<br>`FirstPage1`: The first ad to appear on the right side of the first search results page<br>`FirstPage2`: The second ad to appear on the right side of the first search results page<br>`FirstPage3`: The third ad to appear on the right side of the first search results page<br>`FirstPage4`: The fourth ad to appear on the right side of the first search results page<br>`FirstPage5`: The fifth ad to appear on the right side of the first search results page<br>`FirstPage6`: The sixth ad to appear on the right side of the first search results page<br>`FirstPage7`: The seventh ad to appear on the right side of the first search results page<br>`FirstPage8`: The eighth ad to appear on the right side of the first search results page<br>`FirstPage9`: The ninth ad to appear on the right side of the first search results page<br>`FirstPage10`: The tenth ad to appear on the right side of the first search results page<br>`MainLine1`: The first ad to appear at the top of the search results page<br>`MainLine2`: The second ad to appear at the top of the search results page<br>`MainLine3`: The third ad to appear at the top of the search results page<br>`MainLine4`: The fourth ad to appear at the top of the search results page<br> `clicks`<br>integer<br>*ad clicks*<br>the number of clicks that the keyword and match type generated during the last month<br> `impressions`<br>integer<br>*ad impressions*<br>the number of impressions that the keyword and match type generated during the last month<br> `average_cpc`<br>integer<br>*average cost per click, USD*<br>calculated by dividing the cost of all clicks by the number of clicks<br> `ctr`<br>integer<br>*click-through rate as a percentage*<br>calculated by dividing the number of clicks by the number of impressions and multiplying the result by 100<br> `total_cost`<br>integer<br>*total cost of an ad, USD*<br>the cost of using the specified keyword and match type during the last month<br> `average_bid`<br>integer<br>*average bid of the keyword*<br> **`tablet`**<br>array<br>*keyword data aggregated for tablet devices*<br>if there is no data, then the value is `null`<br> `ad_position`<br>string<br>*represents the position of the relevant ad in SERP*<br>can take the following values:<br>`FirstPage1`: The first ad to appear on the right side of the first search results page<br>`FirstPage2`: The second ad to appear on the right side of the first search results page<br>`FirstPage3`: The third ad to appear on the right side of the first search results page<br>`FirstPage4`: The fourth ad to appear on the right side of the first search results page<br>`FirstPage5`: The fifth ad to appear on the right side of the first search results page<br>`FirstPage6`: The sixth ad to appear on the right side of the first search results page<br>`FirstPage7`: The seventh ad to appear on the right side of the first search results page<br>`FirstPage8`: The eighth ad to appear on the right side of the first search results page<br>`FirstPage9`: The ninth ad to appear on the right side of the first search results page<br>`FirstPage10`: The tenth ad to appear on the right side of the first search results page<br>`MainLine1`: The first ad to appear at the top of the search results page<br>`MainLine2`: The second ad to appear at the top of the search results page<br>`MainLine3`: The third ad to appear at the top of the search results page<br>`MainLine4`: The fourth ad to appear at the top of the search results page<br> `clicks`<br>integer<br>*ad clicks*<br>the number of clicks that the keyword and match type generated during the last month<br> `impressions`<br>integer<br>*ad impressions*<br>the number of impressions that the keyword and match type generated during the last month<br> `average_cpc`<br>integer<br>*average cost per click, USD*<br>calculated by dividing the cost of all clicks by the number of clicks<br> `ctr`<br>integer<br>*click-through rate as a percentage*<br>calculated by dividing the number of clicks by the number of impressions and multiplying the result by 100<br> `total_cost`<br>integer<br>*total cost of an ad, USD*<br>the cost of using the specified keyword and match type during the last month<br> `average_bid`<br>integer<br>*average bid of the keyword*<br> |
| `month` | integer | *indicates the month for which the data is provided for*<br>example:<br>`10`<br> |
| `keyword_kpi` | object | *object containing keyword metrics*<br>if there is no data, then the value is `null` |
| **`desktop`** | array | *keyword data aggregated for desktop devices*<br>if there is no data, then the value is `null` |
| `ad_position` | string | *represents the position of the relevant ad in SERP*<br>can take the following values:<br>`FirstPage1`: The first ad to appear on the right side of the first search results page<br>`FirstPage2`: The second ad to appear on the right side of the first search results page<br>`FirstPage3`: The third ad to appear on the right side of the first search results page<br>`FirstPage4`: The fourth ad to appear on the right side of the first search results page<br>`FirstPage5`: The fifth ad to appear on the right side of the first search results page<br>`FirstPage6`: The sixth ad to appear on the right side of the first search results page<br>`FirstPage7`: The seventh ad to appear on the right side of the first search results page<br>`FirstPage8`: The eighth ad to appear on the right side of the first search results page<br>`FirstPage9`: The ninth ad to appear on the right side of the first search results page<br>`FirstPage10`: The tenth ad to appear on the right side of the first search results page<br>`MainLine1`: The first ad to appear at the top of the search results page<br>`MainLine2`: The second ad to appear at the top of the search results page<br>`MainLine3`: The third ad to appear at the top of the search results page<br>`MainLine4`: The fourth ad to appear at the top of the search results page<br> |
| `clicks` | integer | *ad clicks*<br>the number of clicks that the keyword and match type generated during the last month<br> |
| `impressions` | integer | *ad impressions*<br>the number of impressions that the keyword and match type generated during the last month<br> |
| `average_cpc` | integer | *average cost per click, USD*<br>calculated by dividing the cost of all clicks by the number of clicks<br> |
| `ctr` | integer | *click-through rate as a percentage*<br>calculated by dividing the number of clicks by the number of impressions and multiplying the result by 100<br> |
| `total_cost` | integer | *total cost of an ad, USD*<br>the cost of using the specified keyword and match type during the last month |
| `average_bid` | integer | *average bid of the keyword*<br> |
| **`mobile`** | array | *keyword data aggregated for mobile devices*<br>if there is no data, then the value is `null` |
| `ad_position` | string | *represents the position of the relevant ad in SERP*<br>can take the following values:<br>`FirstPage1`: The first ad to appear on the right side of the first search results page<br>`FirstPage2`: The second ad to appear on the right side of the first search results page<br>`FirstPage3`: The third ad to appear on the right side of the first search results page<br>`FirstPage4`: The fourth ad to appear on the right side of the first search results page<br>`FirstPage5`: The fifth ad to appear on the right side of the first search results page<br>`FirstPage6`: The sixth ad to appear on the right side of the first search results page<br>`FirstPage7`: The seventh ad to appear on the right side of the first search results page<br>`FirstPage8`: The eighth ad to appear on the right side of the first search results page<br>`FirstPage9`: The ninth ad to appear on the right side of the first search results page<br>`FirstPage10`: The tenth ad to appear on the right side of the first search results page<br>`MainLine1`: The first ad to appear at the top of the search results page<br>`MainLine2`: The second ad to appear at the top of the search results page<br>`MainLine3`: The third ad to appear at the top of the search results page<br>`MainLine4`: The fourth ad to appear at the top of the search results page<br> |
| `clicks` | integer | *ad clicks*<br>the number of clicks that the keyword and match type generated during the last month<br> |
| `impressions` | integer | *ad impressions*<br>the number of impressions that the keyword and match type generated during the last month<br> |
| `average_cpc` | integer | *average cost per click, USD*<br>calculated by dividing the cost of all clicks by the number of clicks<br> |
| `ctr` | integer | *click-through rate as a percentage*<br>calculated by dividing the number of clicks by the number of impressions and multiplying the result by 100<br> |
| `total_cost` | integer | *total cost of an ad, USD*<br>the cost of using the specified keyword and match type during the last month |
| `average_bid` | integer | *average bid of the keyword*<br> |
| **`tablet`** | array | *keyword data aggregated for tablet devices*<br>if there is no data, then the value is `null` |
| `ad_position` | string | *represents the position of the relevant ad in SERP*<br>can take the following values:<br>`FirstPage1`: The first ad to appear on the right side of the first search results page<br>`FirstPage2`: The second ad to appear on the right side of the first search results page<br>`FirstPage3`: The third ad to appear on the right side of the first search results page<br>`FirstPage4`: The fourth ad to appear on the right side of the first search results page<br>`FirstPage5`: The fifth ad to appear on the right side of the first search results page<br>`FirstPage6`: The sixth ad to appear on the right side of the first search results page<br>`FirstPage7`: The seventh ad to appear on the right side of the first search results page<br>`FirstPage8`: The eighth ad to appear on the right side of the first search results page<br>`FirstPage9`: The ninth ad to appear on the right side of the first search results page<br>`FirstPage10`: The tenth ad to appear on the right side of the first search results page<br>`MainLine1`: The first ad to appear at the top of the search results page<br>`MainLine2`: The second ad to appear at the top of the search results page<br>`MainLine3`: The third ad to appear at the top of the search results page<br>`MainLine4`: The fourth ad to appear at the top of the search results page<br> |
| `clicks` | integer | *ad clicks*<br>the number of clicks that the keyword and match type generated during the last month<br> |
| `impressions` | integer | *ad impressions*<br>the number of impressions that the keyword and match type generated during the last month<br> |
| `average_cpc` | integer | *average cost per click, USD*<br>calculated by dividing the cost of all clicks by the number of clicks |
| `ctr` | integer | *click-through rate as a percentage*<br>calculated by dividing the number of clicks by the number of impressions and multiplying the result by 100<br> |
| `total_cost` | integer | *total cost of an ad, USD*<br>the cost of using the specified keyword and match type during the last month |
| `average_bid` | integer | *average bid of the keyword*<br> |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Live
*Source: [https://docs.dataforseo.com/v3/keywords_data/bing/keyword_performance/live/](https://docs.dataforseo.com/v3/keywords_data/bing/keyword_performance/live/)*
#### Setting Live ‘Bing Keyword Performance’ Tasks

You can receive a set of keyword performance stats for a group of keywords depending on the specified match type, location and language parameters. Ad position, clicks, impressions, and other keyword metrics are aggregated for the last month for one or all of the following device types: mobile, desktop, tablet.

Generally, Bing provides the updated data after the 3rd day of a month. For example, if you request keyword data on August 1st, 2nd, or 3rd, and data for July is not available yet, you will receive the data for June. After the 4th day of a month when the update is completed by Bing, the `month` field in the `result` array will indicate that data is already provided for the previous calendar month.

You will get information separately for each keyword specified in a POST array.

If your system requires delivering instant results, the Live method is the best solution for you. Unlike the Standard method, this method doesn’t require making separate POST and GET requests to the corresponding endpoints.

If you don’t need to receive data in real-time, you can use the [the Standard method](https://docs.dataforseo.com/v3/keywords_data/bing/keyword_performance/task_post/?php) method of data retrieval. This method requires making separate POST and GET requests, but it’s more affordable. Using this method you can retrieve the results after our system collects them.

POSThttps://api.dataforseo.com/v3/keywords_data/bing/keyword_performance/live

Pricing

Your account will be charged only for setting a task.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/bing-ads) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute. Visit [DataForSEO Help Center](https://dataforseo.com/help-center/best-practices-for-handling-keywords-data-api-requests) to get practical tips for request handling depending on your Keyword Data API payload volume.

You can send up to 2500 keywords in one `keywords` array. Our system will charge your account per request, no matter what number of keywords an array has, the price for 1 or 1000 keywords will be the same.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `keywords` | array | *keywords*<br>**required field**<br>The maximum number of keywords you can specify: 1000<br>The maximum number of characters for each keyword: 80<br>The maximum number of words for each keyword phrase: 10<br>the specified keywords will be converted to lowercase, data will be provided in a separate array<br>learn more about rules and limitations of `keyword` and `keywords` fields in DataForSEO APIs in this [Help Center article](https://dataforseo.com/help-center/rules-and-limitations-of-keyword-and-keywords-fields-in-dataforseo-apis) |
| `device` | string | *device type*<br>optional field<br>specify this field if you want to get the data for a particular device typepossible values: `desktop`, `mobile`, `tablet`, `all`<br>default value: `all` |
| `match` | string | *keywords match type*<br>optional field<br>can take the following values:<br>`aggregate` returns data across all match types;<br>`broad` returns data for all user queries containing the specified keyword with varying word order;<br>`phrase` returns data for all user queries containing the specified keyword with identical word order;<br>`exact` returns data for user query that matches the specified keyword;**Note:** the `aggregate` match type is applied by default |
| `location_name` | string | *full name of search engine location*<br>**required field if you don’t specify** `location_code` or `location_coordinate`<br>**if you use this field, you don’t need to specify `location_code` or `location_coordinate`**<br>you can receive the list of available locations and languages by making a separate request to `https://api.dataforseo.com/v3/keywords_data/bing/keyword_performance/locations_and_languages`<br>example:<br>`"United States"` |
| `location_code` | integer | *search engine location code*<br>**required field if you don’t specify** `location_name` or `location_coordinate`<br>**if you use this field, you don’t need to specify `location_name` or `location_coordinate`**<br>you can receive the list of available locations and languages by making a separate request to `https://api.dataforseo.com/v3/keywords_data/bing/keyword_performance/locations_and_languages`<br>example:<br>`2840` |
| `location_coordinate` | string | *GPS coordinates of a location*<br>**required field if you don’t specify** `location_name` or `location_code`<br>**if you use this field, you don’t need to specify `location_name` or `location_code`**<br>`location_coordinate` parameter should be specified in the *“latitude,longitude”* format<br>**the data will be provided for the country the specified coordinates belong to**<br>example:<br>`52.6178549,-155.352142` |
| `language_name` | string | *full name of search engine language*<br>**required field if you don’t specify** `language_code`<br>**if you use this field, you don’t need to specify `language_code`**<br>you can receive the list of available locations and languages by making a separate request to `https://api.dataforseo.com/v3/keywords_data/bing/keyword_performance/locations_and_languages`<br>example:<br>`English` |
| `language_code` | string | *search engine language code*<br>**required field if you don’t specify** `language_name`<br>you can receive the list of available locations and languages by making a separate request to `https://api.dataforseo.com/v3/keywords_data/bing/keyword_performance/locations_and_languages`<br>example:<br>`"en"` |
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
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `keyword` | string | *keyword in a POST array* |
| `location_code` | integer | *location code in a POST array*<br>if there is no data, then the value is `null` |
| `language_code` | string | *language code in a POST array*<br>if there is no data, then the value is `null` |
| `year` | integer | *indicates the year for which the data is provided for*<br>example:<br>`2020` |
| `month` | integer | *indicates the month for which the data is provided for*<br>example:<br>`10` |
| `keyword_kpi` | object | *object containing keyword metrics*<br>if there is no data, then the value is `null` |
| **`desktop`** | array | *keyword data aggregated for desktop devices*<br>if there is no data, then the value is `null` |
| `ad_position` | string | *represents the position of the relevant ad in SERP*<br>can take the following values:<br>`FirstPage1`: The first ad to appear on the right side of the first search results page<br>`FirstPage2`: The second ad to appear on the right side of the first search results page<br>`FirstPage3`: The third ad to appear on the right side of the first search results page<br>`FirstPage4`: The fourth ad to appear on the right side of the first search results page<br>`FirstPage5`: The fifth ad to appear on the right side of the first search results page<br>`FirstPage6`: The sixth ad to appear on the right side of the first search results page<br>`FirstPage7`: The seventh ad to appear on the right side of the first search results page<br>`FirstPage8`: The eighth ad to appear on the right side of the first search results page<br>`FirstPage9`: The ninth ad to appear on the right side of the first search results page<br>`FirstPage10`: The tenth ad to appear on the right side of the first search results page<br>`MainLine1`: The first ad to appear at the top of the search results page<br>`MainLine2`: The second ad to appear at the top of the search results page<br>`MainLine3`: The third ad to appear at the top of the search results page<br>`MainLine4`: The fourth ad to appear at the top of the search results page |
| `clicks` | integer | *ad clicks*<br>the number of clicks that the keyword and match type generated during the last month |
| `impressions` | integer | *ad impressions*<br>the number of impressions that the keyword and match type generated during the last month |
| `average_cpc` | integer | *average cost per click, USD*<br>calculated by dividing the cost of all clicks by the number of clicks |
| `ctr` | integer | *click-through rate as a percentage*<br>calculated by dividing the number of clicks by the number of impressions and multiplying the result by 100 |
| `total_cost` | integer | *total cost of an ad, USD*<br>the cost of using the specified keyword and match type during the last month |
| `average_bid` | integer | *average bid of the keyword* |
| **`mobile`** | array | *keyword data aggregated for mobile devices*<br>if there is no data, then the value is `null` |
| `ad_position` | string | *represents the position of the relevant ad in SERP*<br>can take the following values:<br>`FirstPage1`: The first ad to appear on the right side of the first search results page<br>`FirstPage2`: The second ad to appear on the right side of the first search results page<br>`FirstPage3`: The third ad to appear on the right side of the first search results page<br>`FirstPage4`: The fourth ad to appear on the right side of the first search results page<br>`FirstPage5`: The fifth ad to appear on the right side of the first search results page<br>`FirstPage6`: The sixth ad to appear on the right side of the first search results page<br>`FirstPage7`: The seventh ad to appear on the right side of the first search results page<br>`FirstPage8`: The eighth ad to appear on the right side of the first search results page<br>`FirstPage9`: The ninth ad to appear on the right side of the first search results page<br>`FirstPage10`: The tenth ad to appear on the right side of the first search results page<br>`MainLine1`: The first ad to appear at the top of the search results page<br>`MainLine2`: The second ad to appear at the top of the search results page<br>`MainLine3`: The third ad to appear at the top of the search results page<br>`MainLine4`: The fourth ad to appear at the top of the search results page |
| `clicks` | integer | *ad clicks*<br>the number of clicks that the keyword and match type generated during the last month |
| `impressions` | integer | *ad impressions*<br>the number of impressions that the keyword and match type generated during the last month |
| `average_cpc` | integer | *average cost per click, USD*<br>calculated by dividing the cost of all clicks by the number of clicks |
| `ctr` | integer | *click-through rate as a percentage*<br>calculated by dividing the number of clicks by the number of impressions and multiplying the result by 100 |
| `total_cost` | integer | *total cost of an ad, USD*<br>the cost of using the specified keyword and match type during the last month |
| `average_bid` | integer | *average bid of the keyword* |
| **`tablet`** | array | *keyword data aggregated for tablet devices*<br>if there is no data, then the value is `null` |
| `ad_position` | string | *represents the position of the relevant ad in SERP*<br>can take the following values:<br>`FirstPage1`: The first ad to appear on the right side of the first search results page<br>`FirstPage2`: The second ad to appear on the right side of the first search results page<br>`FirstPage3`: The third ad to appear on the right side of the first search results page<br>`FirstPage4`: The fourth ad to appear on the right side of the first search results page<br>`FirstPage5`: The fifth ad to appear on the right side of the first search results page<br>`FirstPage6`: The sixth ad to appear on the right side of the first search results page<br>`FirstPage7`: The seventh ad to appear on the right side of the first search results page<br>`FirstPage8`: The eighth ad to appear on the right side of the first search results page<br>`FirstPage9`: The ninth ad to appear on the right side of the first search results page<br>`FirstPage10`: The tenth ad to appear on the right side of the first search results page<br>`MainLine1`: The first ad to appear at the top of the search results page<br>`MainLine2`: The second ad to appear at the top of the search results page<br>`MainLine3`: The third ad to appear at the top of the search results page<br>`MainLine4`: The fourth ad to appear at the top of the search results page |
| `clicks` | integer | *ad clicks*<br>the number of clicks that the keyword and match type generated during the last month |
| `impressions` | integer | *ad impressions*<br>the number of impressions that the keyword and match type generated during the last month |
| `average_cpc` | integer | *average cost per click, USD*<br>calculated by dividing the cost of all clicks by the number of clicks |
| `ctr` | integer | *click-through rate as a percentage*<br>calculated by dividing the number of clicks by the number of impressions and multiplying the result by 100 |
| `total_cost` | integer | *total cost of an ad, USD*<br>the cost of using the specified keyword and match type during the last month |
| `average_bid` | integer | *average bid of the keyword* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Languages
*Source: [https://docs.dataforseo.com/v3/keywords_data/bing/keyword_suggestions_for_url/languages/](https://docs.dataforseo.com/v3/keywords_data/bing/keyword_suggestions_for_url/languages/)*
#### List of Bing Languages for Keyword Suggestions for URL

Pricing

Your account will not be charged for using this API

GEThttps://api.dataforseo.com/v3/keywords_data/bing/keyword_suggestions_for_url/languages

By calling this API you will receive the list of languages supported by Bing Ads API.

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information about available languages.

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
| `language_name` | string | *language name* |
| `language_code` | string | *language code according to [ISO 639-1](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes)* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Task POST
*Source: [https://docs.dataforseo.com/v3/keywords_data/bing/keyword_suggestions_for_url/task_post/](https://docs.dataforseo.com/v3/keywords_data/bing/keyword_suggestions_for_url/task_post/)*
#### Setting ‘Keyword Suggestions For URL’ Tasks

This endpoint provides keyword suggestions based on the content of a given webpage URL. It analyzes the page and returns a list of relevant keywords, along with a confidence score that indicates the probability that the keyword would match a user’s search query.

This is the Standard method of data retrieval. If you don’t need to receive data in real-time, this method is the best option for you. Set a task and retrieve the results when our system collects them. Execution time depends on the system workload.

If your system requires delivering instant results, the [Live method](https://docs.dataforseo.com/v3/keywords_data/bing/keyword_suggestions_for_url/live/) will be a better solution. This method doesn’t require making separate POST and GET requests to the corresponding endpoints.

POSThttps://api.dataforseo.com/v3/keywords_data/bing/keyword_suggestions_for_url/task_post

Pricing

Your account will be charged only for setting a task.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/bing-ads) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). Task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute, with each POST call containing no more than 100 tasks. If your POST call contains over 100 tasks, the tasks over this limit will return the `40006` error. Visit [DataForSEO Help Center](https://dataforseo.com/help-center/best-practices-for-handling-keywords-data-api-requests) to get practical tips for request handling depending on your Keyword Data API payload volume.

You can also retrieve the results of completed tasks using the unique task identifier `id`. Alternatively, we can send them to you as soon as they are ready if you specify the `postback_url` or `pingback_url` when setting a task. Note that if your server doesn’t respond within 10 seconds, the connection will be aborted by timeout, and the task will be transferred to the [tasks_ready](https://docs.dataforseo.com/v3/keywords_data/bing/keyword_suggestions_for_url/tasks_ready/?php) list. The error code and message depend on your server’s configuration.

See [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) to learn more about using pingbacks and postbacks with DataForSEO APIs.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `target` | string | *target URL of the webpage to scan for possible keywords*<br>**required field**<br>maximum length: 2000 characters |
| `language_name` | string | *full name of search engine language*<br>**required field if you don’t specify** `language_code`<br>if you use this field, you don’t need to specify `language_code`<br>you can receive the list of available languages with their language_name by making a separate request to the<br>https://api.dataforseo.com/v3/keywords_data/bing/keyword_suggestions_for_url/languages<br>example:<br>`English` |
| `language_code` | string | *search engine language code*<br>**required field if you don’t specify** `language_name`<br>if you use this field, you don’t need to specify `language_name`<br>you can receive the list of available languages with their language_code by making a separate request to https://api.dataforseo.com/v3/keywords_data/bing/keyword_suggestions_for_url/languages<br>example:<br>`en` |
| `exclude_brands` | boolean | *determines whether the results exclude brand keywords*<br>optional field<br> |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

**Description of the fields in the results array:**

| Field name | Type | Description |
| --- | --- | --- |
| `version` | string | *the current version of the API* |
| `status_code` | integer | *general status code*<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors)<br>**Note:** we strongly recommend designing a necessary system for handling related exceptional or error conditions |
| `status_message` | string | *general informational message*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *general informational message* |
| `time` | string | *execution time, seconds* |
| `cost` | float | *total *tasks* cost, USD* |
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
| `data` | object | *contains the same parameters that you specified in the POST request* |
| ** `result`** | array | *array of results*<br>in this case, the value will be `null` |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Tasks Ready
*Source: [https://docs.dataforseo.com/v3/keywords_data/bing/keyword_suggestions_for_url/tasks_ready/](https://docs.dataforseo.com/v3/keywords_data/bing/keyword_suggestions_for_url/tasks_ready/)*
#### Get ‘Bing Ads Keyword Suggestions For URL’ Completed Tasks

This endpoint is designed to provide you with the list of completed tasks, which haven’t been collected yet. If you use the Standard method without specifying the `postback_url`, you can receive the list of `id` for all completed tasks using this endpoint. Then, you can collect the results using the **‘Task GET’** endpoint.

Learn more about task completion and obtaining a list of completed tasks in [this help center article.](https://dataforseo.com/help-center/completed-tasks)

**Note:** due to the peculiarities of our architecture the queue of completed tasks is updated with a small delay, which can be an issue for high-volume users. If your system requires collecting over 1000 tasks a minute, we recommend using [pingbacks/postbacks](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) instead, and applying the Tasks Ready endpoint only to obtain the IDs of failed postback tasks.

GEThttps://api.dataforseo.com/v3/keywords_data/bing/keyword_suggestions_for_url/tasks_ready

Pricing

Your account will not be charged when receiving results

Each separate task will remain on the list until it is collected. You can make **up to 20 API calls per minute.** With each API call, you can get 1000 tasks completed within three previous days. The list will not contain the tasks which have already been collected and the tasks that were not collected **within the three days** after completion.

Please note that if you specify the `postback_url`, the task will not be in the list of completed tasks. The task can only be found in the list if the request to your server failed, and your server returned HTTP code response less than `200` or higher than `300`.

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
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the parameters passed in the request’s URL* |
| ** `result`** | array | *array of results* |
| `id` | string | *task identifier of the completed task*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `se` | string | *search engine specified when setting the task* |
| `function` | string | *type of the task* |
| `date_posted` | string | *date when the task was posted (in the UTC format)* |
| `endpoint` | string | *URL for collecting the results of the task* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Task GET
*Source: [https://docs.dataforseo.com/v3/keywords_data/bing/keyword_suggestions_for_url/task_get/](https://docs.dataforseo.com/v3/keywords_data/bing/keyword_suggestions_for_url/task_get/)*
#### Get Bing Ads Keyword Suggestions For URL Results by id

This endpoint provides keyword suggestions based on the content of a given webpage URL. It analyzes the page and returns a list of relevant keywords, along with a confidence score that indicates the probability that the keyword would match a user’s search query.

GEThttps://api.dataforseo.com/v3/keywords_data/bing/keyword_suggestions_for_url/task_get/$id

Pricing

Your account will be charged only for posting a task. You can get the results of the task within the next 30 days for free.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/bing-ads) page.

**Description of the fields for sending a request:**

| Field name | Type | Description |
| --- | --- | --- |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format**<br>you will be able to use it within **30 days** to request the results of the task at any time |

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
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array that were returned an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| ** `result`** | array | *array of results*<br>results are sorted in order from keywords with the highest confidence score to those with the lowest confidence score |
| `keyword` | string | *suggested keyword* |
| `confidence_score` | float | *a score from 0.0 to 1.0 that indicates the probability that the keyword would match a user’s search query* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Live
*Source: [https://docs.dataforseo.com/v3/keywords_data/bing/keyword_suggestions_for_url/live/](https://docs.dataforseo.com/v3/keywords_data/bing/keyword_suggestions_for_url/live/)*
#### Setting Live ‘Bing Ads Keyword Suggestions for URL’ Tasks

This endpoint provides keyword suggestions based on the content of a given webpage URL. It analyzes the page and returns a list of relevant keywords, along with a confidence score that indicates the probability that the keyword would match a user’s search query.

If your system requires delivering instant results, the Live method is the best solution for you. Unlike the Standard method, this method doesn’t require making separate POST and GET requests to the corresponding endpoints.

If you don’t need to receive data in real-time, you can use [the Standard method](https://docs.dataforseo.com/v3/keywords_data/bing/keywords_for_site/task_post/) of data retrieval. This method requires making separate POST and GET requests, but it’s more affordable. Using this method you can retrieve the results after our system collects them.

POSThttps://api.dataforseo.com/v3/keywords_data/bing/keyword_suggestions_for_url/live

Pricing

Your account is charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/bing-ads) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute. Visit [DataForSEO Help Center](https://dataforseo.com/help-center/best-practices-for-handling-keywords-data-api-requests) to get practical tips for request handling depending on your Keyword Data API payload volume.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `target` | string | *target URL of the webpage to scan for possible keywords*<br>**required field**<br>maximum length: 2000 characters |
| `language_name` | string | *full name of search engine language*<br>**required field if you don’t specify** `language_code`<br>if you use this field, you don’t need to specify `language_code`<br>you can receive the list of available languages with their language_name by making a separate request to the<br>https://api.dataforseo.com/v3/keywords_data/bing/keyword_suggestions_for_url/languages<br>example:<br>`English` |
| `language_code` | string | *search engine language code*<br>**required field if you don’t specify** `language_name`<br>if you use this field, you don’t need to specify `language_name`<br>you can receive the list of available languages with their language_code by making a separate request to https://api.dataforseo.com/v3/keywords_data/bing/keyword_suggestions_for_url/languages<br>example:<br>`en` |
| `exclude_brands` | boolean | *determines whether the results exclude brand keywords*<br>optional field<br> |

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
| `tasks_error` | integer | *the number of tasks in the **`tasks`** array that were returned an error* |
| **`tasks`** | array | *array of tasks* |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| ** `result`** | array | *array of results*<br>results are sorted in order from keywords with the highest confidence score to those with the lowest confidence score |
| `keyword` | string | *suggested keyword* |
| `confidence_score` | float | *a score from 0.0 to 1.0 that indicates the probability that the keyword would match a user’s search query* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Job Functions
*Source: [https://docs.dataforseo.com/v3/keywords_data/bing/audience_estimation/job_functions/](https://docs.dataforseo.com/v3/keywords_data/bing/audience_estimation/job_functions/)*
#### List of Job Functions for Bing Ads Audience Estimation

Pricing

Your account will not be charged for using this API

GEThttps://api.dataforseo.com/v3/keywords_data/bing/audience_estimation/job_functions

By calling this API you will receive the list of job functions with `job_function_id `supported by Bing Ads Audience Estimation endpoint.

As a response of the API server, you will receive a list of available job functions.

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
| `job_function_id` | integer | *ID of the job function* |
| `job_function_name` | string | *name of the job function* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Industries
*Source: [https://docs.dataforseo.com/v3/keywords_data/bing/audience_estimation/industries/](https://docs.dataforseo.com/v3/keywords_data/bing/audience_estimation/industries/)*
#### List of Industries for Bing Ads Audience Estimation

Pricing

Your account will not be charged for using this API

GEThttps://api.dataforseo.com/v3/keywords_data/bing/audience_estimation/industries

By calling this API you will receive the list of industries with `industry_id `supported by Bing Ads Audience Estimation endpoint.

As a response of the API server, you will receive a list of available industries.

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
| `industry_id` | integer | *ID of the industry* |
| `industry_name` | string | *name of the industry* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Task POST
*Source: [https://docs.dataforseo.com/v3/keywords_data/bing/audience_estimation/task_post/](https://docs.dataforseo.com/v3/keywords_data/bing/audience_estimation/task_post/)*
#### Setting ‘Bing Ads Audience Estimation’ Tasks

This endpoint provides estimated audience size for an ad campaign based on specified targeting criteria. It returns data on the total estimated audience, such as suggested bid and budget for an ad campaign and estimated engagement metrics.

This is the Standard method of data retrieval. If you don’t need to receive data in real-time, this method is the best option for you. Set a task and retrieve the results when our system collects them. Execution time depends on the system workload.

If your system requires delivering instant results, [the Live method](https://docs.dataforseo.com/v3/keywords_data/bing/search_volume/live/) will be a better solution. This method doesn’t require making separate POST and GET requests to the corresponding endpoints.

POSThttps://api.dataforseo.com/v3/keywords_data/bing/audience_estimation/task_post

Pricing

Your account will be charged only for setting a task.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/bing-ads) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). Task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute, with each POST call containing no more than 100 tasks. If your POST call contains over 100 tasks, the tasks over this limit will return the `40006` error. Visit [DataForSEO Help Center](https://dataforseo.com/help-center/best-practices-for-handling-keywords-data-api-requests) to get practical tips for request handling depending on your Keyword Data API payload volume.

You can also retrieve the results of completed tasks using the unique task identifier `id`. Alternatively, we can send them to you as soon as they are ready if you specify the `postback_url` or `pingback_url` when setting a task. Note that if your server doesn’t respond within 10 seconds, the connection will be aborted by timeout, and the task will be transferred to the [tasks_ready](https://docs.dataforseo.com/v3/keywords_data/bing/search_volume/tasks_ready/?php) list. The error code and message depend on your server’s configuration.

See [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) to learn more about using pingbacks and postbacks with DataForSEO APIs.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `location_name` | string | *full name of search engine location*<br>**required field if you don’t specify** `location_code` or `location_coordinate`<br>**if you use this field, you don’t need to specify `location_code` or `location_coordinate`**<br>you can receive the list of available locations of the search engine with their `location_name` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/bing/locations`<br>example:<br>`London,England,United Kingdom` |
| `location_code` | integer | *search engine location code*<br>**required field if you don’t specify** `location_name` or `location_coordinate`<br>**if you use this field, you don’t need to specify `location_name` or `location_coordinate`**<br>you can receive the list of available locations of the search engines with their `location_code` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/bing/locations`<br>example:<br>`2840` |
| `location_coordinate` | string | *GPS coordinates of a location*<br>**required field if you don’t specify** `location_name` or `location_code`<br>**if you use this field, you don’t need to specify `location_name` or `location_code`**<br>`location_coordinate` parameter should be specified in the *“latitude,longitude,radius (in km)”* format<br>**the data will be provided for the country the specified coordinates belong to**<br>example:<br>`29.6821525,-82.4098881,100` |
| `age` | array | *selection of age ranges for targeting*<br>possible values: `eighteen_to_twenty_four`, `fifty_to_sixty_four`, `sixty_five_and_above`, `thirteen_to_seventeen`, `thirty_five_to_forty_nine`, `twenty_five_to_thirty_four`, `unknown`, `zero_to_twelve` |
| `bid` | float | *desired bid setting value in USD*<br>maximum value: 1000 |
| `daily_budget` | float | *daily campaign budget value in USD*<br>maximum value: 10000 |
| `gender` | array | *gender to target*<br>possible values: `male`, `female`, `unknown` |
| `industry` | array | *industry of LinkedIn profile targeting*<br>if you use this field, you can receive the list of available industry names with industry_id by making a separate request to the https://api.dataforseo.com/v3/keywords_data/bing/audience_estimation/industries<br>example: `806301758` |
| `job_function` | array | *job function of LinkedIn profile targeting*<br>if you use this field, you can receive the list of available job function names with job_function_id by making a separate request to the https://api.dataforseo.com/v3/keywords_data/bing/audience_estimation/job_functions<br>example: `806300451` |

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
*Source: [https://docs.dataforseo.com/v3/keywords_data/bing/audience_estimation/tasks_ready/](https://docs.dataforseo.com/v3/keywords_data/bing/audience_estimation/tasks_ready/)*
#### Get ‘Bing Ads Audience Estimation’ Completed Tasks

This endpoint is designed to provide you with the list of completed tasks, which haven’t been collected yet. If you use the Standard method without specifying the `postback_url`, you can receive the list of `id` for all completed tasks using this endpoint. Then, you can collect the results using the **‘Task GET’** endpoint.

Learn more about task completion and obtaining a list of completed tasks in [this help center article.](https://dataforseo.com/help-center/completed-tasks)

**Note:** due to the peculiarities of our architecture the queue of completed tasks is updated with a small delay, which can be an issue for high-volume users. If your system requires collecting over 1000 tasks a minute, we recommend using [pingbacks/postbacks](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) instead, and applying the Tasks Ready endpoint only to obtain the IDs of failed postback tasks.

GEThttps://api.dataforseo.com/v3/keywords_data/bing/audience_estimation/tasks_ready

Pricing

Your account will not be charged when receiving results

Each separate task will remain on the list until it is collected. You can make **up to 20 API calls per minute.** With each API call, you can get 1000 tasks completed within three previous days. The list will not contain the tasks which have already been collected and the tasks that were not collected **within the three days** after completion.

Please note that if you specify the `postback_url`, the task will not be in the list of completed tasks. The task can only be found in the list if the request to your server failed, and your server returned HTTP code response less than `200` or higher than `300`.

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
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the parameters passed in the request’s URL* |
| ** `result`** | array | *array of results* |
| `id` | string | *task identifier of the completed task*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `se` | string | *search engine specified when setting the task* |
| `function` | string | *type of the task* |
| `date_posted` | string | *date when the task was posted (in the UTC format)* |
| `endpoint` | string | *URL for collecting the results of the task* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Task GET
*Source: [https://docs.dataforseo.com/v3/keywords_data/bing/audience_estimation/task_get/](https://docs.dataforseo.com/v3/keywords_data/bing/audience_estimation/task_get/)*
#### Get Bing Ads Audience Estimation Results by id

This endpoint provides estimated audience size for an ad campaign based on specified targeting criteria. It returns data on the total estimated audience, such as suggested bid and budget for an ad campaign and estimated engagement metrics.

GEThttps://api.dataforseo.com/v3/keywords_data/bing/audience_estimation/task_get/$id

Pricing

Your account will be charged only for posting a task. You can get the results of the task within the next 30 days for free.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/bing-ads) page.

**Description of the fields for sending a request:**

| Field name | Type | Description |
| --- | --- | --- |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format**<br>you will be able to use it within **30 days** to request the results of the task at any time |

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
| `status_code` | integer | *status code of the task *<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request<br>* |
| **`result`** | array | *array of results* |
| `est_impressions` | object | *monthly estimated impressions range* |
| `high` | integer | *indicates the upper bound of the range result*<br> |
| `low` | integer | *indicates the lower bound of the range result*<br> |
| `est_audience_size` | object | *monthly estimated reach user count range*<br> |
| `high` | integer | *indicates the upper bound of the range result*<br> |
| `low` | integer | *indicates the lower bound of the range result*<br> |
| `est_clicks` | object | *monthly estimated click count range*<br> |
| `high` | integer | *indicates the upper bound of the range result*<br> |
| `low` | integer | *indicates the lower bound of the range result*<br> |
| `est_spend` | object | *monthly estimated spending range* |
| `high` | integer | *indicates the upper bound of the range result*<br> |
| `low` | integer | *indicates the lower bound of the range result*<br> |
| `est_cost_per_event` | object | *indicates the estimated cost per event with range result*<br> |
| `high` | float | *indicates the upper bound of the range result*<br> |
| `low` | float | *indicates the lower bound of the range result*<br> |
| `est_ctr` | object | *estimated click-through rate range*<br> |
| `high` | float | *indicates the upper bound of the range result*<br> |
| `low` | float | *indicates the lower bound of the range result*<br> |
| `suggested_bid` | float | *suggested bid value under the current targeting*<br> |
| `suggested_budget` | float | *suggested daily budget value under the current targeting and bid* |
| `events_lost_to_bid` | integer | *indicates event lost count due to insufficient input bid*<br> |
| `events_lost_to_budget` | integer | *indicates the event lost count due to insufficient input budget*<br> |
| `est_reach_audience_size` | integer | *monthly estimated user count*<br> |
| `est_reach_impressions` | integer | *monthly estimated impressions*<br> |
| `currency` | integer | *currency name*<br>example: `USDollar` |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Live
*Source: [https://docs.dataforseo.com/v3/keywords_data/bing/audience_estimation/live/](https://docs.dataforseo.com/v3/keywords_data/bing/audience_estimation/live/)*
#### Setting Live ‘Bing Ads Audience Estimation’ Tasks

This endpoint provides estimated audience size for an ad campaign based on specified targeting criteria. It returns data on the total estimated audience, such as suggested bid and budget for an ad campaign and estimated engagement metrics.

If your system requires delivering instant results, the Live method is the best solution for you. Unlike the Standard method, this method doesn’t require making separate POST and GET requests to the corresponding endpoints.

If you don’t need to receive data in real-time, you can use the [Standard method](https://docs.dataforseo.com/v3/keywords_data/bing/search_volume/task_post/) of data retrieval. This method requires making separate POST and GET requests, but it’s more affordable. Using this method you can retrieve the results after our system collects them.

POSThttps://api.dataforseo.com/v3/keywords_data/bing/audience_estimation/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/bing-ads) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute. Visit [DataForSEO Help Center](https://dataforseo.com/help-center/best-practices-for-handling-keywords-data-api-requests) to get practical tips for request handling depending on your Keyword Data API payload volume.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `location_name` | string | *full name of search engine location*<br>**required field if you don’t specify** `location_code` or `location_coordinate`<br>**if you use this field, you don’t need to specify `location_code` or `location_coordinate`**<br>you can receive the list of available locations of the search engine with their `location_name` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/bing/locations`<br>example:<br>`London,England,United Kingdom` |
| `location_code` | integer | *search engine location code*<br>**required field if you don’t specify** `location_name` or `location_coordinate`<br>**if you use this field, you don’t need to specify `location_name` or `location_coordinate`**<br>you can receive the list of available locations of the search engines with their `location_code` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/bing/locations`<br>example:<br>`2840` |
| `location_coordinate` | string | *GPS coordinates of a location*<br>**required field if you don’t specify** `location_name` or `location_code`<br>**if you use this field, you don’t need to specify `location_name` or `location_code`**<br>`location_coordinate` parameter should be specified in the *“latitude,longitude,radius (in km)”* format<br>**the data will be provided for the country the specified coordinates belong to**<br>example:<br>`29.6821525,-82.4098881,100` |
| `age` | array | *selection of age ranges for targeting*<br>possible values: `eighteen_to_twenty_four`, `fifty_to_sixty_four`, `sixty_five_and_above`, `thirteen_to_seventeen`, `thirty_five_to_forty_nine`, `twenty_five_to_thirty_four`, `unknown`, `zero_to_twelve` |
| `bid` | float | *desired bid setting value in USD*<br>maximum value: 1000 |
| `daily_budget` | float | *daily campaign budget value in USD*<br>maximum value: 10000 |
| `gender` | array | *gender to target*<br>possible values: `male`, `female`, `unknown` |
| `industry` | array | *industry of LinkedIn profile targeting*<br>if you use this field, you can receive the list of available industry names with industry_id by making a separate request to the https://api.dataforseo.com/v3/keywords_data/bing/audience_estimation/industries<br>example: `806301758` |
| `job_function` | array | *job function of LinkedIn profile targeting*<br>if you use this field, you can receive the list of available job function names with job_function_id by making a separate request to the https://api.dataforseo.com/v3/keywords_data/bing/audience_estimation/job_functions<br>example: `806300451` |

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
| `status_code` | integer | *status code of the task *<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request<br>* |
| **`result`** | array | *array of results* |
| `est_impressions` | object | *monthly estimated impressions range* |
| `high` | integer | *indicates the upper bound of the range result*<br> |
| `low` | integer | *indicates the lower bound of the range result*<br> |
| `est_audience_size` | object | *monthly estimated reach user count range*<br> |
| `high` | integer | *indicates the upper bound of the range result*<br> |
| `low` | integer | *indicates the lower bound of the range result*<br> |
| `est_clicks` | object | *monthly estimated click count range*<br> |
| `high` | integer | *indicates the upper bound of the range result*<br> |
| `low` | integer | *indicates the lower bound of the range result*<br> |
| `est_spend` | object | *monthly estimated spending range* |
| `high` | integer | *indicates the upper bound of the range result*<br> |
| `low` | integer | *indicates the lower bound of the range result*<br> |
| `est_cost_per_event` | object | *indicates the estimated cost per event with range result*<br> |
| `high` | float | *indicates the upper bound of the range result*<br> |
| `low` | float | *indicates the lower bound of the range result*<br> |
| `est_ctr` | object | *estimated click-through rate range*<br> |
| `high` | float | *indicates the upper bound of the range result*<br> |
| `low` | float | *indicates the lower bound of the range result*<br> |
| `suggested_bid` | float | *suggested bid value under the current targeting*<br> |
| `suggested_budget` | integer | *suggested daily budget value under the current targeting and bid* |
| `events_lost_to_bid` | integer | *indicates event lost count due to insufficient input bid*<br> |
| `events_lost_to_budget` | integer | *indicates the event lost count due to insufficient input budget*<br> |
| `est_reach_audience_size` | integer | *monthly estimated user count*<br> |
| `est_reach_impressions` | integer | *monthly estimated impressions*<br> |
| `currency` | integer | *currency name*<br>example: `USDollar` |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


#### Overview
*Source: [https://docs.dataforseo.com/v3/keywords_data/google_trends/overview/](https://docs.dataforseo.com/v3/keywords_data/google_trends/overview/)*
### Google Trends API: Overview

This API is designed to provide data about the relative popularity rate of keywords, as well as topics and queries related to them.

**Google Trends API** employs the [eponymous Google service](https://trends.google.com/) to supply you with the following data:

- **Keyword popularity rate over time** – relative to the highest rate for the specified time period.
- **Location-specific keyword popularity rate** – relative to the highest rate for the specified region.
- **Related topics** – users searching for the specified keyword also searched for these topics.
- **Related queries** – users searching for the specified keyword also searched for these keywords.

Specifying two or more keywords, you can compare their popularity rates on a relative scale. *However, note that the number of keywords you can compare is limited to five.*

For now, Google Trends API provides data based on the [‘Explore’](https://trends.google.com/trends/explore) feature of Google Trends. You can check keyword trends for Google Search, Google News, Google Images, Google Shopping, and YouTube. We also plan to expand the number of datasources in the nearest future.

##### Methods

Google Trends API supports both **Standard** and **Live** methods of data retrieval. If your system requires delivering instant results, [the Live method](https://docs.dataforseo.com/v3/keywords_data/google_trends/explore/live/) is the best solution for you. Unlike the Standard method, this method doesn’t require making separate POST and GET requests to the corresponding endpoints.

If you don’t need to receive data in real-time, you can use **the Standard method** of data retrieval. The Standard method requires making separate [POST](https://docs.dataforseo.com/v3/keywords_data/google_trends/explore/task_post/) and [GET](https://docs.dataforseo.com/v3/keywords_data/google_trends/explore/task_get/) requests. Using this method, you can retrieve the results after our system collects them.

Alternatively, you can specify `pingback_url` or `postback_url` when setting a task, and we will notify you on completion of tasks or send them to you respectively.

If you need to set several tasks, you can receive the list of `id` for all completed tasks using [‘Tasks Ready’ endpoint](https://docs.dataforseo.com/v3/keywords_data/google_trends/explore/tasks_ready/), and then collect the results of each separate task using [‘Task GET’ endpoint](https://docs.dataforseo.com/v3/keywords_data/google_trends/explore/task_get/).

Learn more about task completion and obtaining a list of completed tasks in [this help center article.](https://dataforseo.com/help-center/completed-tasks)

You can send up to 2000 API calls per minute. Contact us if you would like to raise the limit.

Visit [DataForSEO Help Center](https://dataforseo.com/help-center/best-practices-for-handling-keywords-data-api-requests) to get practical tips for request handling depending on your Keyword Data API payload volume.

##### Cost

The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/google-trends) page.

You can check your spending in your [account dashboard](https://app.dataforseo.com/api-access) or by making a separate call to [the User Data endpoint](https://docs.dataforseo.com/v3/appendix/user_data/?php).

---


#### Locations
*Source: [https://docs.dataforseo.com/v3/keywords_data/google_trends/locations/](https://docs.dataforseo.com/v3/keywords_data/google_trends/locations/)*
#### List of Google Trends Locations

##### **Note:** All locations in Russia and Belarus are no longer supported across all DataForSEO services due to the invasion of Ukraine.

GEThttps://api.dataforseo.com/v3/keywords_data/google_trends/locations

GEThttps://api.dataforseo.com/v3/keywords_data/google_trends/locations/$country

Pricing

Your account will not be charged for using this API

You will receive the list of Google Trends locations by calling this API. You can filter the list of locations by country when setting a task.

You can also [download the full list of supported locations](https://cdn.dataforseo.com/v3/locations/locations_trends_2026_06_10.csv) in the CSV format (last updated 2026-06-10).

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `country` | string | *country ISO code*<br>optional field<br>specify the ISO code if you want to filter the list of locations by country<br>example:<br>`us` |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information about available locations.

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
| `location_code_parent` | integer | *the code of the superordinate location*<br>example:<br>`"location_code": 9041134,<br>"location_name": "Vienna International Airport,Lower Austria,Austria",<br>"location_code_parent": 20044`<br>where `location_code_parent` corresponds to:<br>`"location_code": 20044,<br>"location_name": "Lower Austria,Austria"` |
| `country_iso_code` | string | *ISO country code of the location* |
| `location_type` | string | *location type*<br>possible values according to [Google’s target types](https://developers.google.com/adwords/api/docs/appendix/geotargeting) |
| `geo_name` | string | *google trends location name*<br>you can use this field for matching obtained results with the `location_name` parameter specified in the request |
| `geo_id` | string | *google trends location identifier*<br>you can use this field for matching obtained results with the `location_code` parameter specified in the request |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


#### Languages
*Source: [https://docs.dataforseo.com/v3/keywords_data/google_trends/languages/](https://docs.dataforseo.com/v3/keywords_data/google_trends/languages/)*
#### List of Google Trends Languages

Pricing

Your account will not be charged for using this API

GEThttps://api.dataforseo.com/v3/keywords_data/google_trends/languages

By calling this API you will receive the list of languages supported by Google Trends API.

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information about available languages.

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
| `language_name` | string | *language name* |
| `language_code` | string | *language code according to [ISO 639-1](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes)* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


#### Categories
*Source: [https://docs.dataforseo.com/v3/keywords_data/google_trends/categories/](https://docs.dataforseo.com/v3/keywords_data/google_trends/categories/)*
#### List of Google Trends Categories

Pricing

Your account will not be charged for using this API

GEThttps://api.dataforseo.com/v3/keywords_data/google_trends/categories

By calling this API you will receive the list of categories supported by Google Trends API.

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
| `category_code` | integer | *unique google trends category identifier* |
| `category_name` | string | *name of the google trends category* |
| `category_code_parent` | integer | *the code of the superordinate category*<br>example:<br>`"category_code": 1100,`<br>`"category_name": "Superhero Films",`<br>`"category_code_parent": 1097`<br>where `category_code_parent` corresponds to:<br>`"category_code": 1097,`<br>`"category_name": "Action & Adventure Films"` |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Task POST
*Source: [https://docs.dataforseo.com/v3/keywords_data/google_trends/explore/task_post/](https://docs.dataforseo.com/v3/keywords_data/google_trends/explore/task_post/)*
#### Setting ‘Google Trends Explore’ Tasks

This endpoint will provide you with the keyword popularity data from the ‘Explore’ feature of Google Trends. You can check keyword trends for Google Search, Google News, Google Images, Google Shopping, and YouTube.

This is the Standard method of data retrieval. If you don’t need to receive data in real-time, this method is the best option for you. Set a task and retrieve the results when our system collects them. Execution time depends on the system workload.

**Note:** Due to the limited capacity of the Google Trends service and related restrictions, our system is restricted to the total of 500K daily requests across all Google Trends API endpoints and all users. We recommend that you distribute your requests over several days to avoid data collection errors and ensure stable access to Google Trends data. Learn more on our [Help Center](https://dataforseo.com/help-center/google-trends-api-limits-and-restrictions).

If your system requires delivering instant results, [the Live method](https://docs.dataforseo.com/v3/keywords_data/google_trends/explore/live/) will be a better solution. This method doesn’t require making separate POST and GET requests to the corresponding endpoints.

Historical data for the `web` type: available from `2004-01-01`;
Historical data for other types: available from `2008-01-01`.

POSThttps://api.dataforseo.com/v3/keywords_data/google_trends/explore/task_post

Pricing

Your account will be charged only for setting a task.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/google-trends) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). Task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute, with each POST call containing no more than 100 tasks. If your POST call contains over 100 tasks, the tasks over this limit will return the `40006` error. Visit [DataForSEO Help Center](https://dataforseo.com/help-center/best-practices-for-handling-keywords-data-api-requests) to get practical tips for request handling depending on your Keyword Data API payload volume.

You will get information for every single keyword in an array.

You can send up to 5 keywords in one `keywords` array. Our system will charge your account per request, no matter what number of keywords an array has, the price for 1 or 5 keywords will be the same.

You can also retrieve the results of completed tasks using the unique task identifier `id`. Alternatively, we can send them to you as soon as they are ready if you specify the `postback_url` or `pingback_url` when setting a task. Note that if your server doesn’t respond within 10 seconds, the connection will be aborted by timeout, and the task will be transferred to the [tasks_ready](https://docs.dataforseo.com/v3/keywords_data/google_trends/explore/tasks_ready/?php) list. The error code and message depend on your server’s configuration.

See [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) to learn more about using pingbacks and postbacks with DataForSEO APIs.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `keywords` | array | *keywords*<br>**required field**<br>the maximum number of keywords you can specify: 5<br>the maximum number of characters you can specify in a keyword: 100<br>the minimum number of characters must be greater than 1<br>comma characters (`,`) in the specified keywords will be unset and ignored<br>**Note:** keywords cannot consist of a combination of the following characters: `< > | \ " - + = ~ ! : * ( ) [ ] { }`<br>**Note:** to obtain `google_trends_topics_list` and `google_trends_queries_list` items, specify no more than 1 keyword<br>learn more about rules and limitations of `keyword` and `keywords` fields in DataForSEO APIs in this [Help Center article](https://dataforseo.com/help-center/rules-and-limitations-of-keyword-and-keywords-fields-in-dataforseo-apis) |
| `location_name` | string | *full name of search engine location*<br>optional field<br>if you don’t use this field, you will recieve global results<br>**if you use this field, you don’t need to specify `location_code`**<br>you can use this field as an array to set several locations, each corresponding to a specific keyword – [learn more](https://dataforseo.com/help-center/multiple-locations-in-google-trends-api);<br>you can receive the list of available locations of the search engine with their `location_name` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/google_trends/locations`<br>example:<br>`United Kingdom` |
| `location_code` | integer | *search engine location code*<br>optional field<br>if you don’t use this field, you will recieve global results<br>**if you use this field, you don’t need to specify `location_name`**<br>you can use this field as an array to set several locations, each corresponding to a specific keyword – [learn more](https://dataforseo.com/help-center/multiple-locations-in-google-trends-api);<br>you can receive the list of available locations of the search engines with their `location_code` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/google_trends/locations`<br>example:<br>`2840` |
| `language_name` | string | *full name of search engine language*<br>optional field<br>default value: `English`<br>if you use this field, you don’t need to specify `language_code`<br>you can receive the list of available languages of the search engine with their `language_name` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/google_trends/languages`<br>example:<br>`English` |
| `language_code` | string | *search engine language code*<br>optional field<br>default value: `en`<br>if you use this field, you don’t need to specify `language_name`<br>you can receive the list of available languages of the search engine with their `language_code` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/google_trends/languages`<br>example:<br>`en` |
| `type` | string | *google trends type*<br>optional field<br>if you don’t specify this field, the `web` type will be used by default<br>possible values: `web`, `news`, `youtube`, `images`, `froogle` |
| `category_code` | integer | *google trends search category*<br>optional field<br>if you don’t specify this field, the `0` value will be applied by default and the search will be carried out across all available categories<br>you can receive the list of available categories with their `category_code` by making a separate request to the `https://api.dataforseo.com/v3/keywords_data/google_trends/categories` |
| `date_from` | string | *starting date of the time range*<br>optional field<br>if you don’t specify this field, the current day and month of the preceding year will be used by default<br>minimal value for the `web` type: `2004-01-01`<br>minimal value for other types: `2008-01-01`<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2019-01-15"` |
| `date_to` | string | *ending date of the time range*<br>optional field<br>if you don’t specify this field, the today’s date will be used by default<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2019-01-15"` |
| `time_range` | string | *preset time ranges*<br>optional field<br>if you specify `date_from` or `date_to` parameters, this field will be ignored when setting a task<br>*possible values for all `type` parameters:*<br>`past_hour`, `past_4_hours`, `past_day`, `past_7_days`, `past_30_days`, `past_90_days`, `past_12_months`, `past_5_years`<br>*possible values for `web` only:*<br>`2004_present`<br>*possible values for `news`, `youtube`, `images`, `froogle`:*<br>`2008_present` |
| `item_types` | array | *types of items returned*<br>optional field<br>to speed up the execution of the request, specify one item at a time;<br>possible values:<br>`"google_trends_graph"`, `"google_trends_map"`, `"google_trends_topics_list"`,`"google_trends_queries_list"`<br>default value:<br>`"google_trends_graph"`<br>**Note:** to obtain `google_trends_topics_list` and `google_trends_queries_list` items, specify no more than 1 keyword in the `keywords` field |
| `postback_url` | string | *URL for sending task results*<br>optional field<br>once the task is completed, we will send a POST request with its results compressed in the `gzip` format to the `postback_url` you specified<br>you can use the ‘$id’ string as a `$id` variable and ‘$tag’ as urlencoded `$tag` variable. We will set the necessary values before sending the request.<br>example:<br>`http://your-server.com/postbackscript?id=$id`<br>`http://your-server.com/postbackscript?id=$id&tag=$tag`<br>**Note:** special characters in `postback_url` will be urlencoded;<br>i.a., the `#` character will be encoded into `%23`<br>learn more on our [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) |
| `pingback_url` | string | *notification URL of a completed task*<br>optional field<br>when a task is completed we will notify you by GET request sent to the URL you have specified<br>you can use the ‘$id’ string as a `$id` variable and ‘$tag’ as urlencoded `$tag` variable. We will set the necessary values before sending the request<br>example:<br>`http://your-server.com/pingscript?id=$id`<br>`http://your-server.com/pingscript?id=$id&tag=$tag`<br>**Note:** special characters in `pingback_url` will be urlencoded;<br>i.a., the `#` character will be encoded into `%23`<br>learn more on our [Help Center](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) |
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
*Source: [https://docs.dataforseo.com/v3/keywords_data/google_trends/explore/tasks_ready/](https://docs.dataforseo.com/v3/keywords_data/google_trends/explore/tasks_ready/)*
#### Get ‘Google Trends Explore’ Completed Tasks

This endpoint is designed to provide you with a list of completed tasks, which haven’t been collected yet. If you use the Standard method without specifying the `postback_url`, you can receive the list of `id` for all completed tasks using this endpoint. Then, you can collect the results using the **‘Task GET’** endpoint.

Learn more about task completion and obtaining a list of completed tasks in [this help center article.](https://dataforseo.com/help-center/completed-tasks)

**Note:** due to the peculiarities of our architecture the queue of completed tasks is updated with a small delay, which can be an issue for high-volume users. If your system requires collecting over 1000 tasks a minute, we recommend using [pingbacks/postbacks](https://dataforseo.com/help-center/pingbacks-postbacks-with-dataforseo-api) instead, and applying the Tasks Ready endpoint only to obtain the IDs of failed postback tasks.

GEThttps://api.dataforseo.com/v3/keywords_data/google_trends/explore/tasks_ready

Pricing

Your account will not be charged when receiving results

Each separate task will remain on the list until it is collected. You can make **up to 20 API calls per minute.** With each API call, you can get 1000 tasks completed within three previous days. The list will not contain the tasks which have already been collected and the tasks that were not collected **within the three days** after completion.

Please note that if you specify the `postback_url`, the task will not be in the list of completed tasks. The task can only be found in the list if the request to your server failed, and your server returned HTTP code response less than `200` or higher than `300`.

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
| `status_code` | integer | *status code of the task*<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the parameters passed in the request’s URL* |
| ** `result`** | array | *array of results* |
| `id` | string | *task identifier of the completed task*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format** |
| `se` | string | *search engine specified when setting the task* |
| `function` | string | *type of the task* |
| `date_posted` | string | *date when the task was posted (in the UTC format)* |
| `endpoint` | string | *URL for collecting the results of the task* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Task GET
*Source: [https://docs.dataforseo.com/v3/keywords_data/google_trends/explore/task_get/](https://docs.dataforseo.com/v3/keywords_data/google_trends/explore/task_get/)*
#### Get Google Trends Explore Results by id

This endpoint will provide you with Google Trends data.

GEThttps://api.dataforseo.com/v3/keywords_data/google_trends/explore/task_get/$id

Pricing

Your account will be charged only for posting a task. You can get the results of the task within the next 30 days for free.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/google-trends) page.

**Description of the fields for sending a request:**

| Field name | Type | Description |
| --- | --- | --- |
| `id` | string | *task identifier*<br>**unique task identifier in our system in the [UUID](https://en.wikipedia.org/wiki/Universally_unique_identifier) format**<br>you will be able to use it within **30 days** to request the results of the task at any time |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information specific to the set tasks.

You can also get all available SERP features by making a request to the following [Sandbox](https://docs.dataforseo.com/v3/appendix/sandbox/) URL:
`https://sandbox.dataforseo.com/v3/keywords_data/google_trends/explore/task_get/00000000-0000-0000-0000-000000000000`
The response will include all available items in the Google Trends Explore endpoint with the fields containing dummy data.
You won’t be charged for using [Sandbox](https://docs.dataforseo.com/v3/appendix/sandbox/) endpoints.

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
| `status_code` | integer | *status code of the task *<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request<br>* |
| **`result`** | array | *array of results* |
| `keywords` | array | *keywords in a POST array* |
| `location_code` | integer | *location code in a POST array*<br>if there is no data, then the value is `null` |
| `language_code` | string | *language code in a POST array*<br>if there is no data, then the value is `null` |
| `check_url` | string | *direct URL to the Google Trends results*<br>you can use it to make sure that we provided accurate results |
| `datetime` | string | *date and time when the result was received*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00` |
| `items_count` | integer | *the number of results returned in the **`items`** array* |
| **`items`** | array | *items on the Google Trends page* |
| **‘google_trends_graph’ element in Google Trends** | | |
| `position` | integer | *the alignment of the element in Google Trends*<br>can take the following values: `1`, `2`, `3`, `4`, etc. |
| `type` | string | *type of element = **‘google_trends_graph’***<br> |
| `title` | string | *title of the element in Google Trends* |
| `keywords` | array | *relevant keywords*<br>the data included in the `google_trends_graph` element is based on the keywords listed in this array |
| `data` | array | *Google Trends data for the specified parameters* |
| `date_from` | string | *start date of the corresponding time range*<br>in the UTC format: “yyyy-mm-dd” |
| `date_to` | string | *end date of the corresponding time range*<br>in the UTC format: “yyyy-mm-dd” |
| `timestamp` | integer | *a point in time in the [Unix time format](https://en.wikipedia.org/wiki/Unix_time)* |
| `missing_data` | boolean | *indicates whether the data is unavailable*<br>if `true` the data on the graph in the Google Trends interface is missing and thus labelled with a dotted line``** |
| `values` | array | *relative keyword popularity rate at a specific timestamp*<br>represents the keyword popularity rate over the given time range<br>**if you specify more than one keyword, the values will be averaged to the highest value across all specified keywords**<br>a value of 100 is the peak popularity for the term. A value of 50 means that the term is half as popular. A score of 0 means there was not enough data for this term |
| `averages` | array | **keyword popularity value averaged over the whole time range** |
| **‘google_trends_map’ element in Google Trends** | | |
| `position` | integer | *the alignment of the element in Google Trends*<br>can take the following values: `1`, `2`, `3`, `4`, etc. |
| `type` | string | *type of element = **‘google_trends_map’***<br> |
| `title` | string | *title of the element in Google Trends* |
| `keywords` | array | *relevant keywords*<br>the data included in the `google_trends_map` element is based on the keywords listed in this array<br> |
| `data` | array | *Google Trends data from the corresponding item* |
| `geo_id` | string | *Google Trends location identifier*<br>you can use this field for matching obtained results with location parameters specified in the request<br>example:<br>`US-NY` |
| `geo_name` | string | *Google Trends location name*<br>you can use this field for matching obtained results with location parameters specified in the request |
| `values` | array | *relative keyword popularity rate in a given location*<br>represents the location-specific keyword popularity rate over the given time range<br>**if you specify more than one keyword, the values will be averaged to the highest value across all specified keywords**<br>a value of `100` is the peak popularity for the term<br>a value of `50` means that the term is half as popular<br>a value of `0` means there was not enough data for this term |
| `max_value_index` | integer | *max value among comparable terms*<br>represents the maximum value if you specified more than two keywords in a POST array<br>if you specified only one keyword, the value will be `null` |
| **‘google_trends_topics_list’ element in Google Trends** | | |
| `position` | integer | *the alignment of the element in Google Trends*<br>can take the following values: `1`, `2`, `3`, `4`, etc. |
| `type` | string | *type of element = **‘google_trends_topics_list’***<br> |
| `title` | string | *title of the element in Google Trends* |
| `keywords` | array | *relevant keywords*<br>the data included in the `google_trends_topics_list` element is based on the keywords listed in this array<br> |
| `data` | object | *Google Trends data from the corresponding item* |
| `**top**` | array | *the most popular related topics*<br>represents the list of the most popular related topics |
| `topic_id` | string | *unique topic identifier in Google Trends* |
| `topic_title` | string | *title of the topic* |
| `topic_type` | string | *type of the topic*<br>represents the general type of the topic |
| `value` | string | *search term popularity*<br>represents the popularity of the topic. Scoring is on a relative scale where a value of 100 is the most commonly searched topic and a value of 50 is a topic searched half as often as the most popular term, and so on. |
| `**rising**` | array | *emerging related topics*<br>represents the list of related topics with the biggest increase in search frequency since the last time period |
| `topic_id` | string | *unique topic identifier in Google Trends* |
| `topic_title` | string | *title of the topic* |
| `topic_type` | string | *type of the topic*<br>represents the general type of the topic |
| `value` | string | *increase in the search term popularity*<br>indicates the relative increase in the search term popularity within the given timeframe<br>**the value is provided in percentage (without the *%* sign)** |
| **‘google_trends_queries_list’ element in Google Trends** | | |
| `position` | integer | *the alignment of the element in Google Trends*<br>can take the following values: `1`, `2`, `3`, `4`, etc. |
| `type` | string | *type of element = **‘google_trends_queries_list’***<br> |
| `title` | string | *title of the element in Google Trends* |
| `keywords` | array | *relevant keywords*<br>the data included in the `google_trends_queries_list` element is based on the keywords listed in this array<br> |
| `data` | object | *Google Trends data from the corresponding item* |
| `**top**` | array | *the most popular related topics*<br>represents the list of the most popular related topics |
| `query` | string | *related query* |
| `value` | string | *search term popularity*<br>represents the popularity of the topic. Scoring is on a relative scale where a value of 100 is the most commonly searched topic and a value of 50 is a topic searched half as often as the most popular term, and so on. |
| `**rising**` | array | *emerging related topics*<br>represents the list of related topics with the biggest increase in search frequency since the last time period |
| `query` | string | *related query* |
| `value` | string | *search term popularity*<br>represents the popularity of the topic. Scoring is on a relative scale where a value of 100 is the most commonly searched topic and a value of 50 is a topic searched half as often as the most popular term, and so on. |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


##### Live
*Source: [https://docs.dataforseo.com/v3/keywords_data/google_trends/explore/live/](https://docs.dataforseo.com/v3/keywords_data/google_trends/explore/live/)*
#### Setting Live ‘Google Trends Explore’ Tasks

This endpoint will provide you with the keyword popularity data from the ‘Explore’ feature of Google Trends. You can check keyword trends for Google Search, Google News, Google Images, Google Shopping, and YouTube.

If your system requires delivering instant results, the Live method is the best solution for you. Unlike the Standard method, this method doesn’t require making separate POST and GET requests to the corresponding endpoints.

**Note:** You may receive limit-related errors if over 250 Live ‘Google Trends Explore’ tasks are sent to our system within a minute.

**Note #2:** Due to the limited capacity of the Google Trends service and related restrictions, our system is restricted to the total of 500K daily requests across all Google Trends API endpoints and all users. We recommend that you distribute your requests over several days to avoid data collection errors and ensure stable access to Google Trends data. Learn more on our [Help Center](https://dataforseo.com/help-center/google-trends-api-limits-and-restrictions).

It’s recommended to use the [Standard method](https://docs.dataforseo.com/v3/keywords_data/google_trends/explore/task_post). It allows sending up to 2000 API calls per minute, with each POST call containing up to 100 tasks. The Standard method requires making separate POST and GET requests, but it’s more affordable. Using this method you can retrieve the results after our system collects them.

Historical data for the `web` type: available from `2004-01-01`;
Historical data for other types: available from `2008-01-01`.

POSThttps://api.dataforseo.com/v3/keywords_data/google_trends/explore/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/google-trends) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute. Visit [DataForSEO Help Center](https://dataforseo.com/help-center/best-practices-for-handling-keywords-data-api-requests) to get practical tips for request handling depending on your Keyword Data API payload volume.

You will get information for every single keyword in an array.

You can send up to 5 keywords in one `keywords` array. Our system will charge your account per each request, no matter what number of keywords an array has.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `keywords` | array | *keywords*<br>**required field**<br>the maximum number of keywords you can specify: 5<br>the maximum number of characters you can specify in a keyword: 100<br>the minimum number of characters must be greater than 1<br>comma characters (`,`) in the specified keywords will be unset and ignored<br>**Note:** keywords cannot consist of a combination of the following characters: `< > | \ " - + = ~ ! : * ( ) [ ] { }`<br>**Note:** to obtain `google_trends_topics_list` and `google_trends_queries_list` items, specify no more than 1 keyword<br>learn more about rules and limitations of `keyword` and `keywords` fields in DataForSEO APIs in this [Help Center article](https://dataforseo.com/help-center/rules-and-limitations-of-keyword-and-keywords-fields-in-dataforseo-apis) |
| `location_name` | string | *full name of search engine location*<br>optional field<br>if you don’t use this field, you will recieve global results<br>**if you use this field, you don’t need to specify `location_code`**<br>you can use this field as an array to set several locations, each corresponding to a specific keyword – [learn more](https://dataforseo.com/help-center/multiple-locations-in-google-trends-api);<br>you can receive the list of available locations of the search engine with their `location_name` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/google_trends/locations`<br>example:<br>`United Kingdom` |
| `location_code` | integer | *search engine location code*<br>optional field<br>if you don’t use this field, you will recieve global results<br>**if you use this field, you don’t need to specify `location_name`**<br>you can use this field as an array to set several locations, each corresponding to a specific keyword – [learn more](https://dataforseo.com/help-center/multiple-locations-in-google-trends-api);<br>you can receive the list of available locations of the search engines with their `location_code` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/google_trends/locations`<br>example:<br>`2840` |
| `language_name` | string | *full name of search engine language*<br>optional field<br>default value: `English`<br>if you use this field, you don’t need to specify `language_code`<br>you can receive the list of available languages of the search engine with their `language_name` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/google_trends/languages`<br>example:<br>`English` |
| `language_code` | string | *search engine language code*<br>optional field<br>default value: `en`<br>if you use this field, you don’t need to specify `language_name`<br>you can receive the list of available languages of the search engine with their `language_code` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/google_trends/languages`<br>example:<br>`en` |
| `type` | string | *google trends type*<br>optional field<br>if you don’t specify this field, the `web` type will be used by default<br>possible values: `web`, `news`, `youtube`, `images`, `froogle` |
| `category_code` | integer | *google trends search category*<br>optional field<br>if you don’t specify this field, the `0` value will be applied by default and the search will be carried out across all available categories<br>you can receive the list of available categories with their `category_code` by making a separate request to the `https://api.dataforseo.com/v3/keywords_data/google_trends/categories` |
| `date_from` | string | *starting date of the time range*<br>optional field<br>if you don’t specify this field, the current day and month of the preceding year will be used by default<br>minimal value for the `web` type: `2004-01-01`<br>minimal value for other types: `2008-01-01`<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2019-01-15"` |
| `date_to` | string | *ending date of the time range*<br>optional field<br>if you don’t specify this field, the today’s date will be used by default<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2019-01-15"` |
| `time_range` | string | *preset time ranges*<br>optional field<br>if you specify `date_from` or `date_to` parameters, this field will be ignored when setting a task<br>*possible values for all `type` parameters:*<br>`past_hour`, `past_4_hours`, `past_day`, `past_7_days`, `past_30_days`, `past_90_days`, `past_12_months`, `past_5_years`<br>*possible values for `web` only:*<br>`2004_present`<br>*possible values for `news`, `youtube`, `images`, `froogle`:*<br>`2008_present` |
| `item_types` | array | *types of items returned*<br>optional field<br>to speed up the execution of the request, specify one item at a time;<br>possible values:<br>`"google_trends_graph"`, `"google_trends_map"`, `"google_trends_topics_list"`,`"google_trends_queries_list"`<br>default value:<br>`"google_trends_graph"`<br>**Note:** to obtain `google_trends_topics_list` and `google_trends_queries_list` items, specify no more than 1 keyword in the `keywords` field |
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
| `status_code` | integer | *status code of the task *<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request<br>* |
| **`result`** | array | *array of results* |
| `keywords` | array | *keywords in a POST array* |
| `location_code` | integer | *location code in a POST array*<br>if there is no data, then the value is `null` |
| `language_code` | string | *language code in a POST array*<br>if there is no data, then the value is `null` |
| `check_url` | string | *direct URL to the Google Trends results*<br>you can use it to make sure that we provided accurate results |
| `datetime` | string | *date and time when the result was received*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00` |
| `items_count` | integer | *the number of results returned in the **`items`** array* |
| **`items`** | array | *items on the Google Trends page* |
| **‘google_trends_graph’ element in Google Trends** | | |
| `position` | integer | *the alignment of the element in Google Trends*<br>can take the following values: `1`, `2`, `3`, `4`, etc. |
| `type` | string | *type of element = **‘google_trends_graph’*** |
| `title` | string | *title of the element in Google Trends* |
| `keywords` | array | *relevant keywords*<br>the data included in the `google_trends_graph` element is based on the keywords listed in this array |
| `data` | array | *Google Trends data for the specified parameters* |
| `date_from` | string | *start date of the corresponding time range*<br>in the UTC format: “yyyy-mm-dd” |
| `date_to` | string | *end date of the corresponding time range*<br>in the UTC format: “yyyy-mm-dd” |
| `timestamp` | integer | *a point in time in the [Unix time format](https://en.wikipedia.org/wiki/Unix_time)* |
| `missing_data` | boolean | *indicates whether the data is unavailable*<br>if `true` the data on the graph in the Google Trends interface is missing and thus labelled with a dotted line |
| `values` | integer | *relative keyword popularity rate at a specific timestamp*<br>represents the keyword popularity rate over the given time range<br>**if you specify more than one keyword, the values will be averaged to the highest value across all specified keywords**<br>a value of 100 is the peak popularity for the term. A value of 50 means that the term is half as popular. A score of 0 means there was not enough data for this term |
| `averages` | array | **keyword popularity values averaged over the whole time range** |
| **‘google_trends_map’ element in Google Trends** | | |
| `position` | integer | *the alignment of the element in Google Trends*<br>can take the following values: `1`, `2`, `3`, `4`, etc. |
| `type` | string | *type of element = **‘google_trends_map’*** |
| `title` | string | *title of the element in Google Trends* |
| `keywords` | array | *relevant keywords*<br>the data included in the `google_trends_map` element is based on the keywords listed in this array |
| `data` | array | *Google Trends data from the corresponding item* |
| `geo_id` | string | *Google Trends location identifier*<br>you can use this field for matching obtained results with location parameters specified in the request<br>example:<br>`US-NY` |
| `geo_name` | string | *Google Trends location name*<br>you can use this field for matching obtained results with location parameters specified in the request |
| `values` | integer | *relative keyword popularity rate in a given location*<br>represents the location-specific keyword popularity rate over the given time range<br>**if you specify more than one keyword, the values will be averaged to the highest value across all specified keywords**<br>a value of `100` is the peak popularity for the term<br>a value of `50` means that the term is half as popular<br>a value of `0` means there was not enough data for this term |
| `max_value_index` | integer | *max value among comparable terms*<br>represents the maximum value if you specified more than two keywords in a POST array<br>if you specified only one keyword, the value will be `null` |
| **‘google_trends_topics_list’ element in Google Trends** | | |
| `position` | integer | *the alignment of the element in Google Trends*<br>can take the following values: `1`, `2`, `3`, `4`, etc. |
| `type` | string | *type of element = **‘google_trends_topics_list’*** |
| `title` | string | *title of the element in Google Trends* |
| `keywords` | array | *relevant keywords*<br>the data included in the `google_trends_topics_list` element is based on the keywords listed in this array |
| `data` | object | *Google Trends data from the corresponding item* |
| `**top**` | array | *the most popular related topics*<br>represents the list of the most popular related topics |
| `topic_id` | string | *unique topic identifier in Google Trends* |
| `topic_title` | string | *title of the topic* |
| `topic_type` | string | *type of the topic*<br>represents the general type of the topic |
| `value` | string | *search term popularity*<br>represents the popularity of the topic. Scoring is on a relative scale where a value of 100 is the most commonly searched topic and a value of 50 is a topic searched half as often as the most popular term, and so on. |
| `**rising**` | array | *emerging related topics*<br>represents the list of related topics with the biggest increase in search frequency since the last time period |
| `topic_id` | string | *unique topic identifier in Google Trends* |
| `topic_title` | string | *title of the topic* |
| `topic_type` | string | *type of the topic*<br>represents the general type of the topic |
| `value` | string | *increase in the search term popularity*<br>indicates the relative increase in the search term popularity within the given timeframe<br>**the value is provided in percentage (without the *%* sign)** |
| **‘google_trends_queries_list’ element in Google Trends** | | |
| `position` | integer | *the alignment of the element in Google Trends*<br>can take the following values: `1`, `2`, `3`, `4`, etc. |
| `type` | string | *type of element = **‘google_trends_queries_list’*** |
| `title` | string | *title of the element in Google Trends* |
| `keywords` | array | *relevant keywords*<br>the data included in the `google_trends_queries_list` element is based on the keywords listed in this array |
| `data` | object | *Google Trends data from the corresponding item* |
| `**top**` | array | *the most popular related topics*<br>represents the list of the most popular related topics |
| `query` | string | *related query* |
| `value` | string | *search term popularity*<br>represents the popularity of the topic. Scoring is on a relative scale where a value of 100 is the most commonly searched topic and a value of 50 is a topic searched half as often as the most popular term, and so on. |
| `**rising**` | array | *emerging related topics*<br>represents the list of related topics with the biggest increase in search frequency since the last time period |
| `query` | string | *related query* |
| `value` | string | *search term popularity*<br>represents the popularity of the topic;<br>scoring is on a relative scale where a value of 100 is the most commonly searched topic and a value of 50 is a topic searched half as often as the most popular term, and so on;<br>**the value is provided in percentage (without the *%* sign)** |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


#### Overview
*Source: [https://docs.dataforseo.com/v3/dataforseo_trends/overview/](https://docs.dataforseo.com/v3/dataforseo_trends/overview/)*
### DataForSEO Trends API: Overview

This API is designed to provide insights into keyword popularity trends.

**DataForSEO Trends API** employs our proprietary algorithm to supply you with the keyword popularity rate over time and keyword popularity rate for the specified region. This API serves as a more reliable alternative to Google Trends API.

For now, DataForSEO Trends API provides keyword trends for Google Search, Google News, and Google Shopping. We also plan to expand the number of datasources in the nearest future.

DataForSEO Trends API currently includes the following set of endpoints:

- [Explore](https://docs.dataforseo.com/v3/keywords_data/dataforseo_trends/explore/live/) provides data for building a detailed graph of keyword popularity over a given time range.
- [Subregion Interests](https://docs.dataforseo.com/v3/keywords_data/dataforseo_trends/subregion_interests/live/) allows to measure keyword popularity across specified locations, and compare the popularity of different keywords within a certain location and across all locations.
- [Demography](https://docs.dataforseo.com/v3/keywords_data/dataforseo_trends/demography/live/) serves a breakdown of keyword popularity data by age and gender.
- [Merged Data](https://docs.dataforseo.com/v3/keywords_data/dataforseo_trends/merged_data/live/) delivers comprehensive data from all of the above endpoints combined.

**How our algorithm works:** Our algorithm provides insights into the popularity of specific keywords based on their association with relevant web pages, news articles, or shopping listings, as well as the popularity of each relevant piece of content. We also combine this information with anonymous user web behavior data from various sources. [Learn more on our Help Center.](https://dataforseo.com/help-center/algorithm-dataforseo-trends-api)

Specifying two or more keywords, you can compare their popularity rates on a relative scale. *However, note that the number of keywords you can compare is limited to five.*

##### Methods

DataForSEO Trends API supports only the Live method of data retrieval. It doesn’t require making separate POST and GET requests to the corresponding endpoints and delivers instant results. You can send up to 2000 API calls per minute. Contact us if you would like to raise the limit.

##### Cost

The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/dataforseo-trends-api-pricing) page.

You can check your spending in your [account dashboard](https://app.dataforseo.com/api-access) or by making a separate call to [the User Data endpoint](https://docs.dataforseo.com/v3/appendix/user_data/?php).

---


#### Locations
*Source: [https://docs.dataforseo.com/v3/keywords_data/dataforseo_trends/locations/](https://docs.dataforseo.com/v3/keywords_data/dataforseo_trends/locations/)*
#### List of DataForSEO Trends Locations

##### **Note:** All locations in Russia and Belarus are no longer supported across all DataForSEO services due to the invasion of Ukraine.

GEThttps://api.dataforseo.com/v3/keywords_data/dataforseo_trends/locations

GEThttps://api.dataforseo.com/v3/keywords_data/dataforseo_trends/locations/$country

Pricing

Your account will not be charged for using this API

You will receive the list of DataForSEO Trends locations by calling this API. You can filter the list of locations by country when setting a task. Please note that the minimum geographic scope supported for the DataForSEO Trends API is country level.

You can also [download the full list of supported locations](https://cdn.dataforseo.com/v3/locations/locations_dataforseo_trends_2026_06_10.csv) in the CSV format (last updated 2026-06-10).

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `country` | string | *country ISO code*<br>optional field<br>specify the ISO code if you want to filter the list of locations by country<br>example:<br>`us` |

As a response of the API server, you will receive [JSON](https://en.wikipedia.org/wiki/JSON)-encoded data containing a `tasks` array with the information about available locations.

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
| `location_code_parent` | integer | *the code of the superordinate location*<br>example:<br>`"location_code": 9041134,<br>"location_name": "Vienna International Airport,Lower Austria,Austria",<br>"location_code_parent": 20044`<br>where `location_code_parent` corresponds to:<br>`"location_code": 20044,<br>"location_name": "Lower Austria,Austria"` |
| `country_iso_code` | string | *ISO country code of the location* |
| `location_type` | string | *location type*<br>possible values according to [Google’s target types](https://developers.google.com/adwords/api/docs/appendix/geotargeting) |
| `geo_name` | string | *DataForSEO trends location name*<br>you can use this field for matching obtained results with the `location_name` parameter specified in the request |
| `geo_id` | string | *DataForSEO trends location identifier*<br>you can use this field for matching obtained results with the `location_code` parameter specified in the request |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


#### Explore
*Source: [https://docs.dataforseo.com/v3/keywords_data/dataforseo_trends/explore/live/](https://docs.dataforseo.com/v3/keywords_data/dataforseo_trends/explore/live/)*
#### Setting Live ‘DataForSEO Trends Explore’ Tasks

This endpoint will provide you with the keyword popularity data from DataForSEO Trends. You can check keyword trends for Google Search, Google News, and Google Shopping.

**How our algorithm works:** Our algorithm provides insights into the popularity of specific keywords based on their association with relevant web pages, news articles, or shopping listings, as well as the popularity of each relevant piece of content. We also combine this information with anonymous user web behavior data from various sources. [Learn more on our Help Center.](https://dataforseo.com/help-center/algorithm-dataforseo-trends-api)

You will get information for every single keyword in an array.

You can send up to 5 keywords in one `keywords` array. Our system will charge your account per each request, no matter what number of keywords an array has.

Historical data for the `web` type: available from `2004-01-01`;
Historical data for other types: available from `2008-01-01`.

POSThttps://api.dataforseo.com/v3/keywords_data/dataforseo_trends/explore/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/dataforseo-trends-api-pricing) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute. The maximum number of requests that can be sent simultaneously is limited to 30.
Visit [DataForSEO Help Center](https://dataforseo.com/help-center/best-practices-for-handling-keywords-data-api-requests) to get practical tips for request handling depending on your Keyword Data API payload volume.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `keywords` | array | *keywords*<br>**required field**<br>the maximum number of keywords you can specify: 5<br>learn more about rules and limitations of `keyword` and `keywords` fields in DataForSEO APIs in this [Help Center article](https://dataforseo.com/help-center/rules-and-limitations-of-keyword-and-keywords-fields-in-dataforseo-apis) |
| `location_name` | string | *full name of search engine location*<br>optional field<br>if you don’t use this field, you will recieve global results<br>**if you use this field, you don’t need to specify `location_code`**<br>you can receive the list of available locations of the search engine with their `location_name` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/dataforseo_trends/locations`<br>**note that the data will be provided for the country the specified `location_name` belongs to;**<br>example:<br>`United Kingdom` |
| `location_code` | integer | *search engine location code*<br>optional field<br>if you don’t use this field, you will recieve global results<br>**if you use this field, you don’t need to specify `location_name`**<br>you can receive the list of available locations of the search engines with their `location_code` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/dataforseo_trends/locations`<br>**note that the data will be provided for the country the specified `location_code` belongs to;**<br>example:<br>`2840` |
| `type` | string | *dataforseo trends type*<br>optional field<br>if you don’t specify this field, the `web` type will be used by default<br>possible values: `web`, `news`, `ecommerce` |
| `date_from` | string | *starting date of the time range*<br>optional field<br>if you don’t specify this field, the current day and month of the preceding year will be used by default<br>minimal value for the `web` type: `2004-01-01`<br>minimal value for other types: `2008-01-01`<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2019-01-15"` |
| `date_to` | string | *ending date of the time range*<br>optional field<br>if you don’t specify this field, the today’s date will be used by default<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2019-01-15"` |
| `time_range` | string | *preset time ranges*<br>optional field<br>if you specify `date_from` or `date_to` parameters, this field will be ignored when setting a task<br>*possible values for all `type` parameters:*<br>`past_4_hours`, `past_day`, `past_7_days`, `past_30_days`, `past_90_days`, `past_12_months`, `past_5_years` |
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
| `status_code` | integer | *status code of the task *<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request<br>* |
| **`result`** | array | *array of results* |
| `keywords` | array | *keywords in a POST array* |
| `type` | array | *search engine type in a POST array* |
| `location_code` | integer | *location code in a POST array*<br>if there is no data, then the value is `null` |
| `language_code` | string | *language code in a POST array*<br>if there is no data, then the value is `null` |
| `datetime` | string | *date and time when the result was received*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00` |
| `items_count` | integer | *the number of results returned in the **`items`** array* |
| **`items`** | array | *contains keyword popularity and related data* |
| **‘dataforseo_trends_graph’ element** | | |
| `position` | integer | *the alignment of the element*<br>can take the following values: `1`, `2`, `3`, `4`, etc. |
| `type` | string | *type of element = **‘dataforseo_trends_graph’*** |
| `keywords` | array | *relevant keywords*<br>the data included in the `dataforseo_trends_graph` element is based on the keywords listed in this array |
| `data` | array | *DataForSEO Trends data for the specified parameters* |
| `date_from` | string | *start date of the corresponding time range*<br>in the UTC format: “yyyy-mm-dd” |
| `date_to` | string | *end date of the corresponding time range*<br>in the UTC format: “yyyy-mm-dd” |
| `timestamp` | integer | *a point in time in the [Unix time format](https://en.wikipedia.org/wiki/Unix_time)* |
| `values` | array | *relative keyword popularity rate at a specific timestamp*<br>represents the keyword popularity rate over the given time range<br>**if you specify more than one keyword, the values will be averaged to the highest value across all specified keywords**<br>a value of 100 is the peak popularity for the term. A value of 50 means that the term is half as popular. A score of 0 means there was not enough data for this term |
| `averages` | array | **keyword popularity values averaged over the whole time range** |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


#### Subregion Interests
*Source: [https://docs.dataforseo.com/v3/keywords_data/dataforseo_trends/subregion_interests/live/](https://docs.dataforseo.com/v3/keywords_data/dataforseo_trends/subregion_interests/live/)*
#### Setting Live ‘DataForSEO Trends Subregion Interests’ Tasks

This endpoint will provide you with location-specific keyword popularity data from DataForSEO Trends. You can check keyword trends for Google Search, Google News, and Google Shopping.

Using the data from this endpoint, you can understand how popular a keyword is across all locations, and compare which of the specified keywords is more popular within a certain location and across all locations. Note: if you specify a single keyword, `interests_comparison` object will be `null`.

**How our algorithm works:** Our algorithm provides insights into the popularity of specific keywords based on their association with relevant web pages, news articles, or shopping listings, as well as the popularity of each relevant piece of content. We also combine this information with anonymous user web behavior data from various sources. [Learn more on our Help Center.](https://dataforseo.com/help-center/algorithm-dataforseo-trends-api)

You will get information for every single keyword in an array.

You can send up to 5 keywords in one `keywords` array. Our system will charge your account per each request, no matter what number of keywords an array has.

Historical data for the `web` type: available from `2004-01-01`;
Historical data for other types: available from `2008-01-01`.

POSThttps://api.dataforseo.com/v3/keywords_data/dataforseo_trends/subregion_interests/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/dataforseo-trends-api-pricing) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute. The maximum number of requests that can be sent simultaneously is limited to 30.
Visit [DataForSEO Help Center](https://dataforseo.com/help-center/best-practices-for-handling-keywords-data-api-requests) to get practical tips for request handling depending on your Keyword Data API payload volume.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `keywords` | array | *keywords*<br>**required field**<br>the maximum number of keywords you can specify: 5<br>avoid symbols and special characters (e.g., UTF symbols, emojis);<br>specifying non-Latin characters, you’ll get data for the countries where they are used<br>learn more about rules and limitations of `keyword` and `keywords` fields in DataForSEO APIs in this [Help Center article](https://dataforseo.com/help-center/rules-and-limitations-of-keyword-and-keywords-fields-in-dataforseo-apis) |
| `location_name` | string | *full name of search engine location*<br>optional field<br>if you don’t use this field, you will recieve global results<br>**if you use this field, you don’t need to specify `location_code`**<br>you can receive the list of available locations of the search engine with their `location_name` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/dataforseo_trends/locations`<br>**note that the data will be provided for the country the specified `location_name` belongs to;**<br>example:<br>`United Kingdom` |
| `location_code` | integer | *search engine location code*<br>optional field<br>if you don’t use this field, you will recieve global results<br>**if you use this field, you don’t need to specify `location_name`**<br>you can receive the list of available locations of the search engines with their `location_code` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/dataforseo_trends/locations`<br>**note that the data will be provided for the country the specified `location_code` belongs to;**<br>example:<br>`2840` |
| `type` | string | *dataforseo trends type*<br>optional field<br>if you don’t specify this field, the `web` type will be used by default<br>possible values: `web`, `news`, `ecommerce` |
| `date_from` | string | *starting date of the time range*<br>optional field<br>if you don’t specify this field, the current day and month of the preceding year will be used by default<br>minimal value for the `web` type: `2004-01-01`<br>minimal value for other types: `2008-01-01`<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2019-01-15"` |
| `date_to` | string | *ending date of the time range*<br>optional field<br>if you don’t specify this field, the today’s date will be used by default<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2019-01-15"` |
| `time_range` | string | *preset time ranges*<br>optional field<br>if you specify `date_from` or `date_to` parameters, this field will be ignored when setting a task<br>*possible values for all `type` parameters:*<br>`past_4_hours`, `past_day`, `past_7_days`, `past_30_days`, `past_90_days`, `past_12_months`, `past_5_years` |
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
| `status_code` | integer | *status code of the task *<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request<br>* |
| **`result`** | array | *array of results* |
| `keywords` | array | *keywords in a POST array* |
| `type` | array | *search engine type in a POST array* |
| `location_code` | integer | *location code in a POST array*<br>if there is no data, then the value is `null` |
| `language_code` | string | *language code in a POST array*<br>if there is no data, then the value is `null` |
| `datetime` | string | *date and time when the result was received*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00` |
| `items_count` | integer | *the number of results returned in the **`items`** array* |
| **`items`** | array | *contains keyword popularity and related data* |
| **‘subregion_interests’ element** | | |
| `position` | integer | *the alignment of the element*<br>can take the following values: `1`, `2`, `3`, `4`, etc. |
| `type` | string | *type of element = **‘subregion_interests’*** |
| `keywords` | array | *relevant keywords*<br>the data included in the `interests` and `interests_comparison` is based on the keywords listed in this array |
| `interests` | array | *subregional keyword popuarity data for each specified term* |
| `keyword` | string | *relevant keyword*<br>the data included in the `values` element is based on this keyword |
| `values` | array | *contains data on relative keyword popularity by country or region* |
| `geo_id` | string | *location identifier*<br>you can use this field for matching obtained results with location parameters specified in the request<br>see the full list of available locations with their `geo_id` [here](https://docs.dataforseo.com/v3/keywords_data/dataforseo_trends/locations/) or by making a separate request to `https://api.dataforseo.com/v3/keywords_data/dataforseo_trends/locations`<br>example:<br>`US-NY` |
| `geo_name` | string | *location name*<br>you can use this field for matching obtained results with location parameters specified in the request<br>see the full list of available locations with their `geo_name` [here](https://docs.dataforseo.com/v3/keywords_data/dataforseo_trends/locations/) or by making a separate request to `https://api.dataforseo.com/v3/keywords_data/dataforseo_trends/locations`<br>example:<br>`Andorra` |
| `value` | integer | *relative keyword popularity rate in a given location*<br>represents location-specific keyword popularity rate over the specified time range;<br>using this `value` you can understand how popular a keyword is in one location compared to another location;<br>calculation: we determine the highest popularity value for the relevant keyword across all locations, and then express all other values as a percentage of that highest value (100);<br>a value of `100` is the highest popularity for the term<br>a value of `50` means that the term is half as popular<br>a value of `0` means there was not enough data for this term |
| `interests_comparison` | object | *comparison of data on subregional keyword popularity for the specified parameters*<br>if you specified a single keyword, the value will be `null` |
| `items` | array | *keyword popularity values per location*<br>values in this array represent percentages relative to the maximum value within each region |
| `geo_id` | string | *location identifier*<br>you can use this field for matching obtained results with location parameters specified in the request<br>see the full list of available locations with their `geo_id` [here](https://docs.dataforseo.com/v3/keywords_data/dataforseo_trends/locations/) or by making a separate request to `https://api.dataforseo.com/v3/keywords_data/dataforseo_trends/locations`<br>example:<br>`US-NY` |
| `geo_name` | string | *location name*<br>you can use this field for matching obtained results with location parameters specified in the request<br>see the full list of available locations with their `geo_name` [here](https://docs.dataforseo.com/v3/keywords_data/dataforseo_trends/locations/) or by making a separate request to `https://api.dataforseo.com/v3/keywords_data/dataforseo_trends/locations`<br>example:<br>`Andorra` |
| `values` | array | *keyword popularity rates within a given location*<br>represents location-specific keyword popularity rate over the specified time range;<br>using these values, you can understand which of the specified `keywords` is more popular in the related location;<br>the first value in the array is provided for the first term from the `keywords` array, the second value is provided for the second keyword, and so on;<br>calculation: we determine the highest popularity value across all specified keywords within a given location, and then express the popularity values of each keyword as a percentage of the highest value (100);<br>a value of `100` is the peak popularity for the term<br>a value of `50` means that the term is half as popular<br>a value of `0` means there was not enough data for this term |
| `absolute_items` | array | *keyword popularity rates across all locations*<br>values in this array represent percentages relative to the maximum value across all locations |
| `geo_id` | string | *location identifier*<br>you can use this field for matching obtained results with location parameters specified in the request<br>see the full list of available locations with their `geo_id` [here](https://docs.dataforseo.com/v3/keywords_data/dataforseo_trends/locations/) or by making a separate request to `https://api.dataforseo.com/v3/keywords_data/dataforseo_trends/locations`<br>example:<br>`US-NY` |
| `geo_name` | string | *location name*<br>you can use this field for matching obtained results with location parameters specified in the request<br>see the full list of available locations with their `geo_name` [here](https://docs.dataforseo.com/v3/keywords_data/dataforseo_trends/locations/) or by making a separate request to `https://api.dataforseo.com/v3/keywords_data/dataforseo_trends/locations`<br>example:<br>`Andorra` |
| `values` | array | *keyword popularity rates relative to all locations*<br>represents location-specific keyword popularity rate over the specified time range;<br>using these values, you can understand how popular each `keyword` is compared to all other keywords across all locations;<br>the first value in the array is provided for the first term from the `keywords` array, the second value is provided for the second keyword, and so on;<br>calculation: we determine the highest popularity value across all keywords across all locations, and then express all other values as a percentage of that highest value (100);<br>a value of `100` is the peak popularity for the term<br>a value of `50` means that the term is half as popular<br>a value of `0` means there was not enough data for this term |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


#### Demography
*Source: [https://docs.dataforseo.com/v3/keywords_data/dataforseo_trends/demography/live/](https://docs.dataforseo.com/v3/keywords_data/dataforseo_trends/demography/live/)*
#### Setting Live ‘DataForSEO Trends Demography’ Tasks

This endpoint will provide you with the demographic breakdown (by age and gender) of keyword popularity per each specified term based on DataForSEO Trends data. You can check keyword trends for Google Search, Google News, and Google Shopping.

**How our algorithm works:** Our algorithm provides insights into the popularity of specific keywords based on their association with relevant web pages, news articles, or shopping listings, as well as the popularity of each relevant piece of content. We also combine this information with anonymous user web behavior data from various sources. [Learn more on our Help Center.](https://dataforseo.com/help-center/algorithm-dataforseo-trends-api)

You will get information for every single keyword in an array.

You can send up to 5 keywords in one `keywords` array. Our system will charge your account per each request, no matter what number of keywords an array has.

Historical data for the `web` type: available from `2004-01-01`;
Historical data for other types: available from `2008-01-01`.

POSThttps://api.dataforseo.com/v3/keywords_data/dataforseo_trends/demography/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/dataforseo-trends-api-pricing) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute. The maximum number of requests that can be sent simultaneously is limited to 30.
Visit [DataForSEO Help Center](https://dataforseo.com/help-center/best-practices-for-handling-keywords-data-api-requests) to get practical tips for request handling depending on your Keyword Data API payload volume.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `keywords` | array | *keywords*<br>**required field**<br>the maximum number of keywords you can specify: 5<br>avoid symbols and special characters (e.g., UTF symbols, emojis);<br>specifying non-Latin characters, you’ll get data for the countries where they are used<br>learn more about rules and limitations of `keyword` and `keywords` fields in DataForSEO APIs in this [Help Center article](https://dataforseo.com/help-center/rules-and-limitations-of-keyword-and-keywords-fields-in-dataforseo-apis) |
| `location_name` | string | *full name of search engine location*<br>optional field<br>if you don’t use this field, you will recieve global results<br>**if you use this field, you don’t need to specify `location_code`**<br>you can receive the list of available locations of the search engine with their `location_name` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/dataforseo_trends/locations`<br>**note that the data will be provided for the country the specified `location_name` belongs to;**<br>example:<br>`United Kingdom` |
| `location_code` | integer | *search engine location code*<br>optional field<br>if you don’t use this field, you will recieve global results<br>**if you use this field, you don’t need to specify `location_name`**<br>you can receive the list of available locations of the search engines with their `location_code` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/dataforseo_trends/locations`<br>**note that the data will be provided for the country the specified `location_code` belongs to;**<br>example:<br>`2840` |
| `type` | string | *dataforseo trends type*<br>optional field<br>if you don’t specify this field, the `web` type will be used by default<br>possible values: `web`, `news`, `ecommerce` |
| `date_from` | string | *starting date of the time range*<br>optional field<br>if you don’t specify this field, the current day and month of the preceding year will be used by default<br>minimal value for the `web` type: `2004-01-01`<br>minimal value for other types: `2008-01-01`<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2019-01-15"` |
| `date_to` | string | *ending date of the time range*<br>optional field<br>if you don’t specify this field, the today’s date will be used by default<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2019-01-15"` |
| `time_range` | string | *preset time ranges*<br>optional field<br>if you specify `date_from` or `date_to` parameters, this field will be ignored when setting a task<br>*possible values for all `type` parameters:*<br>`past_4_hours`, `past_day`, `past_7_days`, `past_30_days`, `past_90_days`, `past_12_months`, `past_5_years` |
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
| `status_code` | integer | *status code of the task *<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request<br>* |
| **`result`** | array | *array of results* |
| `keywords` | array | *keywords in a POST array* |
| `type` | array | *search engine type in a POST array* |
| `location_code` | integer | *location code in a POST array*<br>if there is no data, then the value is `null` |
| `language_code` | string | *language code in a POST array*<br>if there is no data, then the value is `null` |
| `datetime` | string | *date and time when the result was received*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00` |
| `items_count` | integer | *the number of results returned in the **`items`** array* |
| **`items`** | array | *contains keyword popularity and related data* |
| **‘demography’ element** | | |
| `position` | integer | *the alignment of the element*<br>can take the following values: `1`, `2`, `3`, `4`, etc. |
| `type` | string | *type of element = **‘demography’*** |
| `keywords` | array | *relevant keywords*<br>the data included in the `demography` and `demography_comparison` is based on the keywords listed in this array |
| `demography` | object | *demographic breakdown of keyword popularity data per each specified term*<br>conains keyword popularity data by age and gender |
| `age` | array | *distribution of keyword popularity by age* |
| `keyword` | string | *relevant keyword for which demographic data is provided* |
| `values` | array | *contains age range and corresponding keyword popularity values* |
| `type` | string | *age range*<br>can take the following values: `18-24`, `25-34`, `35-44`, `45-54`, `55-64` |
| `value` | integer | *keyword popularity rate within the specified age range*<br>using this `value` you can understand how popular a keyword is within each age range;<br>calculation: we determine the highest popularity value for the relevant keyword across all age groups, and then express all other values as a percentage of that highest value (100);<br>a value of `100` is the highest popularity for the term<br>a value of `0` means there was not enough data for this term |
| `gender` | array | *distribution of keyword popularity by gender* |
| `keyword` | string | *relevant keyword for which demographic data is provided* |
| `values` | array | *contains gender and corresponding keyword popularity values* |
| `type` | string | *gender category*<br>can take the following values: `female`, `male` |
| `value` | integer | *keyword popularity rate within the specified gender category*<br>using this `value` you can understand how popular a keyword is within each gender category;<br>calculation: we determine the highest popularity value for the relevant keyword across all gender categories, and then express all other values as a percentage of that highest value (100);<br>a value of `100` is the highest popularity for the term;<br>a value of `0` means there was not enough data for this term |
| `demography_comparison` | object | *comparison of demographic data on keyword popularity for the specified parameters*<br>conains keyword popularity data by age and gender<br>if you specified a single keyword, the value will be `null` |
| `age` | object | *comparison of keyword popularity data by age* |
| `$18-24` | array | *indicates age range and contains corresponding keyword popularity values*<br>contains comparison of keyword popularity for the specified terms within the specified age range<br>**variable can take the following values:** `18-24`, `25-34`, `35-44`, `45-54`, `55-64`;<br>using the values from this array, you can understand which of the specified `keywords` is more popular within the related age range;<br>the first value in the array is provided for the first term from the `keywords` array, the second value is provided for the second keyword, and so on;<br>calculation: we determine the total popularity value of all keywords within each age range, and then express all other values as a percentage of the total value (100);<br>a value of `100` is the highest popularity for the term<br>a value of `0` means there was not enough data for this term |
| `gender` | object | *comparison of keyword popularity data by gender* |
| `female` | array | *indicates gender category and contains corresponding keyword popularity values*<br>contains comparison of keyword popularity for the specified terms within the specified gender category;<br>using the values from this array, you can understand which of the specified `keywords` is more popular within the related gender category;<br>the first value in the array is provided for the first term from the `keywords` array, the second value is provided for the second keyword, and so on;<br>calculation: we determine the total popularity value of all keywords within each gender category, and then express all other values as a percentage of the total value (100);<br>a value of `100` is the highest popularity for the term<br>a value of `0` means there was not enough data for this term |
| `male` | array | *indicates gender category and contains corresponding keyword popularity values*<br>contains comparison of keyword popularity for the specified terms within the specified gender category;<br>using the values from this array, you can understand which of the specified `keywords` is more popular within the related gender category;<br>the first value in the array is provided for the first term from the `keywords` array, the second value is provided for the second keyword, and so on;<br>calculation: we determine the total popularity value of all keywords within each gender category, and then express all other values as a percentage of the total value (100);<br>a value of `100` is the highest popularity for the term<br>a value of `0` means there was not enough data for this term |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


#### Merged Data
*Source: [https://docs.dataforseo.com/v3/keywords_data/dataforseo_trends/merged_data/live/](https://docs.dataforseo.com/v3/keywords_data/dataforseo_trends/merged_data/live/)*
#### Setting Live ‘DataForSEO Trends Merged Data’ Tasks

This endpoint will provide you with the keyword popularity data from DataForSEO Trends. In addition to keyword popularity rate over the given time range, you will get location-specific keyword popularity data, and a demographic breakdown of keyword popularity per each specified term along with comparative values.

You can check keyword trends for Google Search, Google News, and Google Shopping.

**How our algorithm works:** Our algorithm provides insights into the popularity of specific keywords based on their association with relevant web pages, news articles, or shopping listings, as well as the popularity of each relevant piece of content. We also combine this information with anonymous user web behavior data from various sources. [Learn more on our Help Center.](https://dataforseo.com/help-center/algorithm-dataforseo-trends-api)

You will get information for every single keyword in an array.

You can send up to 5 keywords in one `keywords` array. Our system will charge your account per each request, no matter what number of keywords an array has.

Historical data for the `web` type: available from `2004-01-01`;
Historical data for other types: available from `2008-01-01`.

POSThttps://api.dataforseo.com/v3/keywords_data/dataforseo_trends/merged_data/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/dataforseo-trends-api-pricing) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute. The maximum number of requests that can be sent simultaneously is limited to 30.
Visit [DataForSEO Help Center](https://dataforseo.com/help-center/best-practices-for-handling-keywords-data-api-requests) to get practical tips for request handling depending on your Keyword Data API payload volume.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `keywords` | array | *keywords*<br>**required field**<br>the maximum number of keywords you can specify: 5<br>avoid symbols and special characters (e.g., UTF symbols, emojis);<br>specifying non-Latin characters, you’ll get data for the countries where they are used<br>learn more about rules and limitations of `keyword` and `keywords` fields in DataForSEO APIs in this [Help Center article](https://dataforseo.com/help-center/rules-and-limitations-of-keyword-and-keywords-fields-in-dataforseo-apis) |
| `location_name` | string | *full name of search engine location*<br>optional field<br>if you don’t use this field, you will recieve global results<br>**if you use this field, you don’t need to specify `location_code`**<br>you can receive the list of available locations of the search engine with their `location_name` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/dataforseo_trends/locations`<br>**note that the data will be provided for the country the specified `location_name` belongs to;**<br>example:<br>`United Kingdom` |
| `location_code` | integer | *search engine location code*<br>optional field<br>if you don’t use this field, you will recieve global results<br>**if you use this field, you don’t need to specify `location_name`**<br>you can receive the list of available locations of the search engines with their `location_code` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/dataforseo_trends/locations`<br>**note that the data will be provided for the country the specified `location_code` belongs to;**<br>example:<br>`2840` |
| `type` | string | *dataforseo trends type*<br>optional field<br>if you don’t specify this field, the `web` type will be used by default<br>possible values: `web`, `news`, `ecommerce` |
| `date_from` | string | *starting date of the time range*<br>optional field<br>if you don’t specify this field, the current day and month of the preceding year will be used by default<br>minimal value for the `web` type: `2004-01-01`<br>minimal value for other types: `2008-01-01`<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2019-01-15"` |
| `date_to` | string | *ending date of the time range*<br>optional field<br>if you don’t specify this field, the today’s date will be used by default<br>date format: `"yyyy-mm-dd"`<br>example:<br>`"2019-01-15"` |
| `time_range` | string | *preset time ranges*<br>optional field<br>if you specify `date_from` or `date_to` parameters, this field will be ignored when setting a task<br>*possible values for all `type` parameters:*<br>`past_4_hours`, `past_day`, `past_7_days`, `past_30_days`, `past_90_days`, `past_12_months`, `past_5_years` |
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
| `status_code` | integer | *status code of the task *<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of response codes [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request<br>* |
| **`result`** | array | *array of results* |
| `keywords` | array | *keywords in a POST array* |
| `type` | array | *search engine type in a POST array* |
| `location_code` | integer | *location code in a POST array*<br>if there is no data, then the value is `null` |
| `language_code` | string | *language code in a POST array*<br>if there is no data, then the value is `null` |
| `datetime` | string | *date and time when the result was received*<br>in the UTC format: “yyyy-mm-dd hh-mm-ss +00:00”<br>example:<br>`2019-11-15 12:57:46 +00:00` |
| `items_count` | integer | *the number of results returned in the **`items`** array* |
| **`items`** | array | *contains keyword popularity and related data* |
| **‘dataforseo_trends_graph’ element** | | |
| `position` | integer | *the alignment of the element*<br>can take the following values: `1`, `2`, `3`, `4`, etc. |
| `type` | string | *type of element = **‘dataforseo_trends_graph’*** |
| `keywords` | array | *relevant keywords*<br>the data included in the `dataforseo_trends_graph` element is based on the keywords listed in this array |
| `data` | array | *DataForSEO Trends data for the specified parameters* |
| `date_from` | string | *start date of the corresponding time range*<br>in the UTC format: “yyyy-mm-dd” |
| `date_to` | string | *end date of the corresponding time range*<br>in the UTC format: “yyyy-mm-dd” |
| `timestamp` | integer | *a point in time in the [Unix time format](https://en.wikipedia.org/wiki/Unix_time)* |
| `values` | array | *relative keyword popularity rate at a specific timestamp*<br>**if you specify more than one keyword, the values will be averaged to the highest value across all specified keywords**<br>a value of `100` is the peak popularity for the term<br>a value of `50` means that the term is half as popular<br>a value of `0` means there was not enough data for this term |
| `averages` | array | **keyword popularity values averaged over the whole time range** |
| **‘subregion_interests’ element** | | |
| `position` | integer | *the alignment of the element*<br>can take the following values: `1`, `2`, `3`, `4`, etc. |
| `type` | string | *type of element = **‘subregion_interests’*** |
| `keywords` | array | *relevant keywords*<br>the data included in the `interests` and `interests_comparison` is based on the keywords listed in this array |
| `interests` | array | *subregional keyword popuarity data for each specified term* |
| `keyword` | string | *relevant keyword*<br>the data included in the `values` element is based on this keyword |
| `values` | array | *contains data on relative keyword popularity by country or region* |
| `geo_id` | string | *location identifier*<br>you can use this field for matching obtained results with location parameters specified in the request<br>see the full list of available locations with their `geo_id` [here](https://docs.dataforseo.com/v3/keywords_data/dataforseo_trends/locations/) or by making a separate request to `https://api.dataforseo.com/v3/keywords_data/dataforseo_trends/locations`<br>example:<br>`US-NY` |
| `geo_name` | string | *location name*<br>you can use this field for matching obtained results with location parameters specified in the request<br>see the full list of available locations with their `geo_name` [here](https://docs.dataforseo.com/v3/keywords_data/dataforseo_trends/locations/) or by making a separate request to `https://api.dataforseo.com/v3/keywords_data/dataforseo_trends/locations`<br>example:<br>`Andorra` |
| `value` | integer | *relative keyword popularity rate in a given location*<br>represents location-specific keyword popularity rate over the specified time range;<br>using this `value` you can understand how popular a keyword is in one location compared to another location;<br>calculation: we determine the highest popularity value for the relevant keyword across all locations, and then express all other values as a percentage of that highest value (100);<br>a value of `100` is the highest popularity for the term<br>a value of `50` means that the term is half as popular<br>a value of `0` means there was not enough data for this term |
| `interests_comparison` | object | *comparison of data on subregional keyword popularity for the specified parameters*<br>if you specified a single keyword, the value will be `null` |
| `items` | array | *keyword popularity values per location*<br>values in this array represent percentages relative to the maximum value within each region |
| `geo_id` | string | *location identifier*<br>you can use this field for matching obtained results with location parameters specified in the request<br>see the full list of available locations with their `geo_id` [here](https://docs.dataforseo.com/v3/keywords_data/dataforseo_trends/locations/) or by making a separate request to `https://api.dataforseo.com/v3/keywords_data/dataforseo_trends/locations`<br>example:<br>`US-NY` |
| `geo_name` | string | *location name*<br>you can use this field for matching obtained results with location parameters specified in the request<br>see the full list of available locations with their `geo_name` [here](https://docs.dataforseo.com/v3/keywords_data/dataforseo_trends/locations/) or by making a separate request to `https://api.dataforseo.com/v3/keywords_data/dataforseo_trends/locations`<br>example:<br>`Andorra` |
| `values` | array | *keyword popularity rates within a given location*<br>represents location-specific keyword popularity rate over the specified time range;<br>using these values, you can understand which of the specified `keywords` is more popular in the related location;<br>the first value in the array is provided for the first term from the `keywords` array, the second value is provided for the second keyword, and so on;<br>calculation: we determine the highest popularity value across all specified keywords within a given location, and then express the popularity values of each keyword as a percentage of the highest value (100);<br>a value of `100` is the peak popularity for the term<br>a value of `50` means that the term is half as popular<br>a value of `0` means there was not enough data for this term |
| `absolute_items` | array | *keyword popularity rates across all locations*<br>values in this array represent percentages relative to the maximum value across all locations |
| `geo_id` | string | *location identifier*<br>you can use this field for matching obtained results with location parameters specified in the request<br>see the full list of available locations with their `geo_id` [here](https://docs.dataforseo.com/v3/keywords_data/dataforseo_trends/locations/) or by making a separate request to `https://api.dataforseo.com/v3/keywords_data/dataforseo_trends/locations`<br>example:<br>`US-NY` |
| `geo_name` | string | *location name*<br>you can use this field for matching obtained results with location parameters specified in the request<br>see the full list of available locations with their `geo_name` [here](https://docs.dataforseo.com/v3/keywords_data/dataforseo_trends/locations/) or by making a separate request to `https://api.dataforseo.com/v3/keywords_data/dataforseo_trends/locations`<br>example:<br>`Andorra` |
| `values` | array | *keyword popularity rates relative to all locations*<br>represents location-specific keyword popularity rate over the specified time range;<br>using these values, you can understand how popular each `keyword` is compared to all other keywords across all locations;<br>the first value in the array is provided for the first term from the `keywords` array, the second value is provided for the second keyword, and so on;<br>calculation: we determine the highest popularity value across all keywords across all locations, and then express all other values as a percentage of that highest value (100);<br>a value of `100` is the peak popularity for the term<br>a value of `50` means that the term is half as popular<br>a value of `0` means there was not enough data for this term |
| **‘demography’ element** | | |
| `position` | integer | *the alignment of the element*<br>can take the following values: `1`, `2`, `3`, `4`, etc. |
| `type` | string | *type of element = **‘demography’*** |
| `keywords` | array | *relevant keywords*<br>the data included in the `demography` and `demography_comparison` is based on the keywords listed in this array |
| `demography` | object | *demographic breakdown of keyword popularity data per each specified term*<br>conains keyword popularity data by age and gender |
| `age` | array | *distribution of keyword popularity by age* |
| `keyword` | string | *relevant keyword for which demographic data is provided* |
| `values` | array | *contains age range and corresponding keyword popularity values* |
| `type` | string | *age range*<br>can take the following values: `18-24`, `25-34`, `35-44`, `45-54`, `55-64` |
| `value` | integer | *keyword popularity rate within the specified age range*<br>using this `value` you can understand how popular a keyword is within each age range;<br>calculation: we determine the highest popularity value for the relevant keyword across all age groups, and then express all other values as a percentage of that highest value (100);<br>a value of `100` is the highest popularity for the term<br>a value of `0` means there was not enough data for this term |
| `gender` | array | *distribution of keyword popularity by gender* |
| `keyword` | string | *relevant keyword for which demographic data is provided* |
| `values` | array | *contains gender and corresponding keyword popularity values* |
| `type` | string | *gender category*<br>can take the following values: `female`, `male` |
| `value` | integer | *keyword popularity rate within the specified gender category*<br>using this `value` you can understand how popular a keyword is within each gender category;<br>calculation: we determine the highest popularity value for the relevant keyword across all gender categories, and then express all other values as a percentage of that highest value (100);<br>a value of `100` is the highest popularity for the term;<br>a value of `0` means there was not enough data for this term |
| `demography_comparison` | object | *comparison of demographic data on keyword popularity for the specified parameters*<br>conains keyword popularity data by age and gender<br>if you specified a single keyword, the value will be `null` |
| `age` | object | *comparison of keyword popularity data by age* |
| `$18-24` | array | *indicates age range and contains corresponding keyword popularity values*<br>contains comparison of keyword popularity for the specified terms within the specified age range<br>**variable can take the following values:** `18-24`, `18-24`, `25-34`, `35-44`, `45-54`, `55-64`;<br>using the values from this array, you can understand which of the specified `keywords` is more popular within the related age range;<br>the first value in the array is provided for the first term from the `keywords` array, the second value is provided for the second keyword, and so on;<br>calculation: we determine the total popularity value of all keywords within each age range, and then express all other values as a percentage of the total value (100);<br>a value of `100` is the highest popularity for the term<br>a value of `0` means there was not enough data for this term |
| `gender` | object | *comparison of keyword popularity data by gender* |
| `female` | array | *indicates gender category and contains corresponding keyword popularity values*<br>contains comparison of keyword popularity for the specified terms within the specified gender category;<br>using the values from this array, you can understand which of the specified `keywords` is more popular within the related gender category;<br>the first value in the array is provided for the first term from the `keywords` array, the second value is provided for the second keyword, and so on;<br>calculation: we determine the total popularity value of all keywords within each gender category, and then express all other values as a percentage of the total value (100);<br>a value of `100` is the highest popularity for the term<br>a value of `0` means there was not enough data for this term |
| `male` | array | *indicates gender category and contains corresponding keyword popularity values*<br>contains comparison of keyword popularity for the specified terms within the specified gender category;<br>using the values from this array, you can understand which of the specified `keywords` is more popular within the related gender category;<br>the first value in the array is provided for the first term from the `keywords` array, the second value is provided for the second keyword, and so on;<br>calculation: we determine the total popularity value of all keywords within each gender category, and then express all other values as a percentage of the total value (100);<br>a value of `100` is the highest popularity for the term<br>a value of `0` means there was not enough data for this term |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


#### Overview
*Source: [https://docs.dataforseo.com/v3/keywords_data/clickstream_data/overview/](https://docs.dataforseo.com/v3/keywords_data/clickstream_data/overview/)*
### Clickstream Data API: Overview

This API provides clickstream-based search volume and other keyword insights.

**DataForSEO Clickstream Data API is based on clickstream data and provides a reliable and innovative alternative to search volume from Google Ads. **

DataForSEO Clickstream Data API currently includes the following set of endpoints:

- [Global Search Volume](https://docs.dataforseo.com/v3/keywords_data/clickstream_data/global_search_volume/live/) provides clickstream-based search volume data for up to 1000 keywords with geographical distribution across all available locations;
- [DataForSEO Search Volume](https://docs.dataforseo.com/v3/keywords_data/clickstream_data/dataforseo_search_volume/live/) will provide you with search volume normalized with Bing search volume data or clickstream data for up to 1000 keywords in a single request;
- [Bulk Clickstream Search Volume](https://docs.dataforseo.com/v3/keywords_data/clickstream_data/bulk_search_volume/live/) is designed to provide clickstream-based search volume data for up to 1000 keywords in a single Live request with historical monthly values for up to 12 months;
- [Locations and Languages](https://docs.dataforseo.com/v3/keywords_data/clickstream_data/locations_and_languages/) provides a list of available locations and languages.

**How our algorithm works:** our algorithm is based on refined clickstream data from reliable providers. Using special multipliers derived from multiple factors, we turn raw clickstream data into actionable keyword metrics. You can learn more about how we calculate clickstream-based metrics in [this Help Center article](https://dataforseo.com/help-center/what-are-clickstream-based-metrics-and-how-do-we-calculate-them).

##### Methods

DataForSEO Clickstream Data API supports only the Live method of data retrieval. It doesn’t require making separate POST and GET requests to the corresponding endpoints and delivers instant results. You can send up to 2000 API calls per minute. Contact us if you would like to raise the limit.

##### Cost

The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/clickstream-api-pricing) page.

You can check your spending in your [account dashboard](https://app.dataforseo.com/api-access) or by making a separate call to [the User Data endpoint](https://docs.dataforseo.com/v3/appendix/user_data/?php).

---


#### Locations and Languages
*Source: [https://docs.dataforseo.com/v3/keywords_data/clickstream_data/locations_and_languages/](https://docs.dataforseo.com/v3/keywords_data/clickstream_data/locations_and_languages/)*
#### List of Locations and Languages for DataForSEO Clickstream Data API

Using this endpoint you can get the full list of locations and languages supported in DataForSEO Clickstream Data API.

##### **Note:** All locations in Russia and Belarus are no longer supported across all DataForSEO services due to the invasion of Ukraine.

GEThttps://api.dataforseo.com/v3/keywords_data/clickstream_data/locations_and_languages

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
| `location_code_parent` | integer | *the code of the superordinate location*<br>the value will be `null` as `Country` is the only supported `location_type` for this API |
| `country_iso_code` | string | *ISO country code of the location* |
| `location_type` | string | *location type*<br>possible values:<br>`Country` |
| `available_languages` | array | *supported languages*<br>contains the languages which are supported for a specific location |
| `language_name` | string | *language name* |
| `language_code` | string | *language code according to [ISO 639-1](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes)* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


#### DataForSEO Search Volume
*Source: [https://docs.dataforseo.com/v3/keywords_data/clickstream_data/dataforseo_search_volume/live/](https://docs.dataforseo.com/v3/keywords_data/clickstream_data/dataforseo_search_volume/live/)*
#### Setting Live ‘DataForSEO Search Volume’ Tasks

This endpoint will provide you with search volume normalized with Bing search volume data or clickstream data for up to 1000 keywords in a single request.

POSThttps://api.dataforseo.com/v3/keywords_data/clickstream_data/dataforseo_search_volume/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/clickstream-api-pricing) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute. Visit [DataForSEO Help Center](https://dataforseo.com/help-center/best-practices-for-handling-keywords-data-api-requests) to get practical tips for request handling depending on your Keyword Data API payload volume.

You will get information for every single keyword in an array.

**Note that you can send no more than 12 requests per minute per account due certain limitations beyond our control.**

You can send up to 1000 keywords in one `keywords` array. Our system will charge your account per each request, no matter what number of keywords an array has, the price for 1 or 1000 keywords will be the same.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `keywords` | array | *target keywords*<br>**required field**<br>UTF-8 encoding<br>maximum number of keywords you can specify in this array: 1000<br>the keywords will be converted to lowercase format<br>**Note:** certain symbols and characters (e.g., UTF symbols, emojis) are not allowed<br>to learn more about which symbols and characters can be used, please refer to [this article](https://dataforseo.com/help-center/using-symbols-in-keywords-when-setting-a-google-ads-task)<br>learn more about rules and limitations of `keyword` and `keywords` fields in DataForSEO APIs in this [Help Center article](https://dataforseo.com/help-center/rules-and-limitations-of-keyword-and-keywords-fields-in-dataforseo-apis) |
| `location_name` | string | *full name of search engine location*<br>**required field if you don’t specify `location_code `**<br>you can receive the list of available locations with `location_name` by making a separate request to `https://api.dataforseo.com/v3/keywords_data/clickstream_data/locations_and_languages`<br>example:<br>`United Kingdom` |
| `location_code` | integer | *search engine location code*<br>**required field if you don’t specify `location_name`**<br>if you use this field, you can receive the list of available locations with `location_code` by making a separate request to the `https://api.dataforseo.com/v3/keywords_data/clickstream_data/locations_and_languages`<br>example:<br>`2826` |
| `language_name` | string | *full name of search engine language*<br>**required field if don’t specify `language_code`**<br>you can receive the list of available languages with their `language_name` by making a separate request to the `https://api.dataforseo.com/v3/keywords_data/clickstream_data/locations_and_languages`<br>example:<br>`English` |
| `language_code` | string | *search engine language code*<br>**required field if don’t specify `language_name`**<br>you can receive the list of available languages with their `language_code` by making a separate request to the `https://api.dataforseo.com/v3/keywords_data/clickstream_data/locations_and_languages`<br>example:<br>`en` |
| `use_clickstream` | boolean | *use clickstream data to provide results*<br>optional field<br>if set to `true`, you will get DataForSEO search volume values based on clickstream data;<br>if set to `false`, Bing search volume data will be used to calculate DataForSEO search volume;<br>default value: `true`;<br>**Note:** Bing search volume is available for locations provided in [Bing Search Volume History Locations](https://docs.dataforseo.com/v3/keywords_data/bing/search_volume_history/locations_and_languages/?bash) and [Bing Ads Locations](https://docs.dataforseo.com/v3/keywords_data/bing/locations/?bash) endpoints; search volume values for any other location are calculated based on clickstream data even if you set this parameter to `false`<br> |
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
| `status_code` | integer | *status code of the task *<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | array | *contains the same parameters that you specified in the POST request<br>* |
| **`result`** | array | *array of results* |
| `location_code` | string | *location code in a POST array*<br>if there is no data, then the value is `null` |
| `language_code` | string | *language code in a POST array<br>*<br>**Note:**if the keyword in the POST array appears to be misspelled, data will be returned for the correctly spelled keyword;<br>we use the functionality of Google Ads API to check and validate the spelling of keywords, [learn more by this link](https://support.google.com/google-ads/answer/7476658) |
| `location_code` | integer | *location code in a POST array*<br>if there is no data, then the value is `null` |
| `language_code` | string | *language code in a POST array*<br>if there is no data, then the value is `null` |
| `items_count` | string | *ithe number of results returned in the `items` array* |
| `items` | array | *array of keywords*<br>contains keywords and their search volume rates |
| `keyword` | string | *keyword provided in the POST array* |
| `use_clickstream` | boolean | *indicates if the `use_clickstream` parameter is active*<br>possible values: `true`, `false` |
| `search_volume` | integer | *current search volume rate of a keyword* |
| `monthly_searches` | array | *monthly search volume rates*<br>array of objects with search volume rates in a certain month of a year |
| `year` | integer | *year* |
| `month` | integer | *month* |
| `search_volume` | integer | *search volume rate in a certain month of a year* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


#### Global Search Volume
*Source: [https://docs.dataforseo.com/v3/keywords_data/clickstream_data/global_search_volume/live/](https://docs.dataforseo.com/v3/keywords_data/clickstream_data/global_search_volume/live/)*
#### Setting Live ‘Clickstream Global Search Volume’ Tasks

The Clickstream Global Search Volume endpoint of DataForSEO Keywords Data API is designed to provide clickstream-based search volume data for up to 1000 keywords in a single Live request. What’s more, it offers geographical distribution of clickstream search volume values across all available locations.

You can learn more about this endpoint in [this Help Center article](https://dataforseo.com/help-center/what-is-global-search-volume).

POSThttps://api.dataforseo.com/v3/keywords_data/clickstream_data/global_search_volume/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/clickstream-api-pricing) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute. The maximum number of requests that can be sent simultaneously is limited to 30.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `keywords` | array | *target keywords*<br>**required field**<br>UTF-8 encoding<br>maximum number of keywords you can specify in this array: 1000;<br>each keyword should be at least 3 characters long;<br>the keywords will be converted to lowercase format;<br>**Note:** certain symbols and characters (e.g., UTF symbols, emojis) are not allowed<br>to learn more about which symbols and characters can be used, please refer to [this article](https://dataforseo.com/help-center/using-symbols-in-keywords-when-setting-a-google-ads-task)<br>learn more about rules and limitations of `keyword` and `keywords` fields in DataForSEO APIs in this [Help Center article](https://dataforseo.com/help-center/rules-and-limitations-of-keyword-and-keywords-fields-in-dataforseo-apis) |
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
| `status_code` | integer | *status code of the task *<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `items_count` | integer | *the number of results returned in the `items` array* |
| `**items**` | array | *contains keywords and related data* |
| `keyword` | string | *keyword*<br>**keyword is returned with decoded %## (plus symbol ‘+’ will be decoded to a space character)** |
| `search_volume` | integer | *clickstream-based average monthly search volume rate*<br>represents the (approximate) number of searches for the given keyword idea based on clickstream<br>you can learn more about clickstream search volume in [this Help Center article](https://dataforseo.com/help-center/what-is-clickstream-search-volume-and-how-to-get-it-with-dataforseo) |
| `country_distribution` | array | *distribution of clickstream by countries*<br>represents clickstream-based search volume in available countries, as well as its respective percentage of global search volume |
| `country_iso_code` | string | *country ISO code* |
| `search_volume` | integer | *search volume in a given country* |
| `percentage` | float | *percentage of global search volume* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---


#### Bulk Search Volume
*Source: [https://docs.dataforseo.com/v3/keywords_data/clickstream_data/bulk_search_volume/live/](https://docs.dataforseo.com/v3/keywords_data/clickstream_data/bulk_search_volume/live/)*
#### Setting Live ‘Bulk Clickstream Search Volume’ Tasks

The Bulk Clickstream Search Volume endpoint of DataForSEO Keywords Data API is designed to provide clickstream-based search volume data for up to 1000 keywords in a single Live request. What’s more, it offers historical search volume values for up to 12 months (depending on keywords, location, and language parameters).

You can learn more about this endpoint in [this Help Center article](https://dataforseo.com/help-center/what-is-clickstream-search-volume-and-how-to-get-it-with-dataforseo).

POSThttps://api.dataforseo.com/v3/keywords_data/clickstream_data/bulk_search_volume/live

Pricing

Your account will be charged for each request.
The cost can be calculated on the [Pricing](https://dataforseo.com/pricing/keywords-data/clickstream-api-pricing) page.

All POST data should be sent in the [JSON](https://en.wikipedia.org/wiki/JSON) format (UTF-8 encoding). The task setting is done using the POST method. When setting a task, you should send all task parameters in the task array of the generic POST array. You can send up to 2000 API calls per minute. The maximum number of requests that can be sent simultaneously is limited to 30.

Below you will find a detailed description of the fields you can use for setting a task.

**Description of the fields for setting a task:**

| Field name | Type | Description |
| --- | --- | --- |
| `keywords` | array | *target keywords*<br>**required field**<br>UTF-8 encoding<br>maximum number of keywords you can specify in this array: 1000;<br>each keyword should be at least 3 characters long;<br>the keywords will be converted to lowercase format;<br>**Note:** certain symbols and characters (e.g., UTF symbols, emojis) are not allowed<br>to learn more about which symbols and characters can be used, please refer to [this article](https://dataforseo.com/help-center/using-symbols-in-keywords-when-setting-a-google-ads-task)<br>learn more about rules and limitations of `keyword` and `keywords` fields in DataForSEO APIs in this [Help Center article](https://dataforseo.com/help-center/rules-and-limitations-of-keyword-and-keywords-fields-in-dataforseo-apis) |
| `location_name` | string | *full name of the location*<br>**required field if you don’t specify** `location_code`<br>**Note:** it is required to specify either `location_name` or `location_code`<br>you can receive the list of available locations with their `location_name` by making a separate request to the<br>`https://api.dataforseo.com/v3/keywords_data/clickstream_data/locations_and_languages`<br>example:<br>`United Kingdom` |
| `location_code` | integer | *location code*<br>**required field if you don’t specify** `location_name`<br>**Note:** it is required to specify either `location_name` or `location_code`<br>you can receive the list of available locations with their `location_code` by making a separate request to the<br>`https://api.dataforseo.com/v3/keywords_data/clickstream_data/locations_and_languages`<br>example:<br>`2840` |
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
| `status_code` | integer | *status code of the task *<br>generated by DataForSEO; can be within the following range: 10000-60000<br>you can find the full list of the response codes [here](https://docs.dataforseo.com/v3/appendix/errors) |
| `status_message` | string | *informational message of the task*<br>you can find the full list of general informational messages [here](https://docs.dataforseo.com/v3/appendix-errors/) |
| `time` | string | *execution time, seconds* |
| `cost` | float | *cost of the task, USD* |
| `result_count` | integer | *number of elements in the `result` array* |
| `path` | array | *URL path* |
| `data` | object | *contains the same parameters that you specified in the POST request* |
| **`result`** | array | *array of results* |
| `location_code` | integer | *location code in a POST array* |
| `items_count` | integer | *the number of results returned in the `items` array* |
| `**items**` | array | *contains keywords and related data* |
| `keyword` | string | *keyword*<br>**keyword is returned with decoded %## (plus character ‘+’ will be decoded to a space character)** |
| `search_volume` | integer | *clickstream-based average monthly search volume rate*<br>represents the (approximate) number of searches for the given keyword idea based on clickstream<br>you can learn more about clickstream search volume in [this Help Center article](https://dataforseo.com/help-center/what-is-clickstream-search-volume-and-how-to-get-it-with-dataforseo) |
| `monthly_searches` | array | *monthly searches*<br>represents the (approximate) number of searches on this keyword idea (as available for the past twelve months), targeted to the specified geographic locations |
| `year` | integer | *year* |
| `month` | integer | *month* |
| `search_volume` | integer | *monthly average search volume rate* |

> Instead of ‘login’ and ‘password’ use your credentials from https://app.dataforseo.com/api-access

> The above command returns JSON structured like this:

---
