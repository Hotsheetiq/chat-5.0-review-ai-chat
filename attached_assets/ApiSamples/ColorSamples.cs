using LCS.UI.API.QuickStart.Examples.Helpers;
using LCS.UI.API.QuickStart.Examples.Models;
using Newtonsoft.Json.Linq;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace LCS.UI.API.QuickStart.Examples.ApiSamples
{
   public class ColorSamples
   {
      static public async Task GetAllReturningModels()
      {
         List<ColorModel> colors = await HttpClientHelper.GetCollectionReturningModels<ColorModel>("/colors");
      }

      static public async Task GetAllReturningJson()
      {
         JArray colors = await HttpClientHelper.GetCollectionReturningJsonArray("/colors");
      }

      static public async Task GetReturningModel()
      {
         ColorModel color = await HttpClientHelper.GetSingleReturningModel<ColorModel>("/colors/1");
      }

      static public async Task GetReturningJson()
      {
         JObject color = await HttpClientHelper.GetSingleReturningJson("/colors/1");
      }

      static public async Task Update()
      {
         // Get
         ColorModel colorForUpdate = await HttpClientHelper.GetSingleReturningModel<ColorModel>("/colors/1?embeds=EntityTypes");

         // Changed and Post
         colorForUpdate.Name = "Red1";
         ColorModel colorUpdated = await HttpClientHelper.PostSingle<ColorModel>("/colors?embeds=EntityTypes", colorForUpdate);
      }

      static public async Task UpdateCollection()
      {
         // Get
         ColorModel color1 = await HttpClientHelper.GetSingleReturningModel<ColorModel>("/colors/1?embeds=EntityTypes");
         ColorModel color2 = await HttpClientHelper.GetSingleReturningModel<ColorModel>("/colors/2?embeds=EntityTypes");

         color1.Name = "Red2";
         color2.Name = "White2";

         List<ColorModel> colorsForUpdate = new List<ColorModel>
         {
            color1,
            color2
         };

         // Changed and Post
         List<ColorModel> colorsUpdated = await HttpClientHelper.PostCollection<ColorModel>("/colors?embeds=EntityTypes", colorsForUpdate);
      }
   }
}
