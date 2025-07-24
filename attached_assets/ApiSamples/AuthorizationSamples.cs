using LCS.UI.API.QuickStart.Examples.Helpers;
using LCS.UI.API.QuickStart.Examples.Models;
using System.Net.Http;
using System.Threading.Tasks;

namespace LCS.UI.API.QuickStart.Examples.ApiSamples
{
   public class AuthorizationSamples
   {
      static public string ApiToken { get; set; }

      static public async Task Authorize()
      {
         // Replace Username, Password, and Location ID with those supplied by LCS.
         UserAuthorizationModel uam = new UserAuthorizationModel
         {
            Username = "username",
            Password = "password",
            LocationID = 1
         };

         HttpResponseMessage response = await HttpClientHelper.Client.PostAsJsonAsync("/Authentication/AuthorizeUser", uam);
         response.EnsureSuccessStatusCode();
         ApiToken = response.Content.ReadAsStringAsync().Result.Trim('"');
         HttpClientHelper.AddApiToken(ApiToken);
      }
   }
}
