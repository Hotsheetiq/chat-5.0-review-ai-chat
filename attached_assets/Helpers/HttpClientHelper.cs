using Newtonsoft.Json.Linq;
using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Threading.Tasks;

namespace LCS.UI.API.QuickStart.Examples.Helpers
{
   internal class HttpClientHelper
   {
      // Singleton for HttpClient
      private static HttpClient _client;
      internal static HttpClient Client
      {
         get
         {
            if (_client == null)
            {
               _client = new HttpClient();
               _client.BaseAddress = new Uri("https://corporateID.api.rentmanager.com/");      // <--- Where corporateId is the identifier assigned to your company by LCS.
               _client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));
            }
            return _client;
         }
      }

      // Add the RM Api Security Token to the client request's header
      static internal void AddApiToken(string apiToken)
      {
         _client.DefaultRequestHeaders.Add("X-RM12Api-ApiToken", apiToken);
      }

      // Generic Get.  Returns a single <T> model
      static internal async Task<T> GetSingleReturningModel<T>(string url)
      {
         T item;
         HttpResponseMessage response = await HttpClientHelper.Client.GetAsync(url);
         try
         {
            response.EnsureSuccessStatusCode();
            item = response.Content.ReadAsAsync<T>().Result;
         }
         catch (HttpRequestException ex)
         {
            if (response.StatusCode == System.Net.HttpStatusCode.NotFound)
            {
               item = default(T);
            }
            else
            {
               throw ex;
            }
         }
         return item;
      }

      // Generic Get.  Returns a Json object
      static internal async Task<JObject> GetSingleReturningJson(string url)
      {
         HttpResponseMessage response = await HttpClientHelper.Client.GetAsync(url);
         response.EnsureSuccessStatusCode();
         JObject item = response.Content.ReadAsAsync<JObject>().Result;
         return item;
      }

      // Generic Get All.  Returns a list of <T> models
      static internal async Task<List<T>> GetCollectionReturningModels<T>(string url)
      {
         List<T> items;
         HttpResponseMessage response = await HttpClientHelper.Client.GetAsync(url);
         try
         {
            response.EnsureSuccessStatusCode();
            items = response.Content.ReadAsAsync<List<T>>().Result;
         }
         catch (HttpRequestException ex)
         {
            if (response.StatusCode == System.Net.HttpStatusCode.NotFound)
            {
               items = new List<T>();
            }
            else
            {
               throw ex;
            }
         }
         return items;
      }

      // Generic Get All.  Returns a JSon Array
      static internal async Task<JArray> GetCollectionReturningJsonArray(string url)
      {
         HttpResponseMessage response = await HttpClientHelper.Client.GetAsync(url);
         response.EnsureSuccessStatusCode();
         JArray items = response.Content.ReadAsAsync<JArray>().Result;
         return items;
      }

      // Generic Post single model.  Returns a single model.
      static internal async Task<T> PostSingle<T>(string url, T updateModel)
      {
         // Post requires list
         List<T> updateModels = new List<T>
         {
            updateModel
         };

         // Convert to string
         string data = Newtonsoft.Json.JsonConvert.SerializeObject(updateModels);

         HttpResponseMessage response = await HttpClientHelper.Client.PostAsync(url, new StringContent(data, Encoding.UTF8, "application/json"));
         response.EnsureSuccessStatusCode();

         // Result is also a list
         List<T> items = response.Content.ReadAsAsync<List<T>>().Result;
         if (items.Count > 0)
         {
            return items[0];
         }
         else
         {
            return default(T);
         }
      }

      // Generic post podel list.  Returns a model list.
      static internal async Task<List<T>> PostCollection<T>(string url, List<T> updateModels)
      {
         // Convert to string
         string data = Newtonsoft.Json.JsonConvert.SerializeObject(updateModels);

         HttpResponseMessage response = await HttpClientHelper.Client.PostAsync(url, new StringContent(data, Encoding.UTF8, "application/json"));
         response.EnsureSuccessStatusCode();

         // Result is also a list
         List<T> items = response.Content.ReadAsAsync<List<T>>().Result;
         return items;
      }
   }
}
