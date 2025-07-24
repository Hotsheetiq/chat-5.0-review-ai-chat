using LCS.UI.API.QuickStart.Examples.Helpers;
using Newtonsoft.Json.Linq;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Threading.Tasks;

namespace LCS.UI.API.QuickStart.Examples.ApiSamples
{
   public class ReportSamples
   {
      static public async Task GetBalanceDueReportAsPdfAndSaveToDisk(int propertyID)
      {
         HttpResponseMessage response = await HttpClientHelper.Client.GetAsync($"/Reports/82/RunReport?parameters=PropertyIDs,{propertyID}&GetOptions=ReturnPDFStream");
         try
         {
            response.EnsureSuccessStatusCode();
         }
         catch (HttpRequestException ex)
         {
            if (response.StatusCode == System.Net.HttpStatusCode.NotFound)
            {
               return;
            }
            else
            {
               throw ex;
            }
         }

         string reportPath = Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments);
         string reportFile = reportPath + @"\BalanceDue.pdf";

         Stream reportStream = response.Content.ReadAsStreamAsync().Result;
         if (reportStream.GetType().Name == "MemoryStream")
         {
            if (File.Exists(reportFile))
            {
               File.Delete(reportFile);
            }

            Stream fileStream = File.Create(reportFile);
            reportStream.CopyTo(fileStream);

            fileStream.Close();
            reportStream.Close();
         }
      }

      static public async Task GetBalanceDueReportAsPdfAndSaveToDiskAndLaunchInViewer(int propertyID)
      {
         HttpResponseMessage response = await HttpClientHelper.Client.GetAsync($"/Reports/82/RunReport?parameters=PropertyIDs,{propertyID}&GetOptions=ReturnPDFStream");
         try
         {
            response.EnsureSuccessStatusCode();
         }
         catch (HttpRequestException ex)
         {
            if (response.StatusCode == System.Net.HttpStatusCode.NotFound)
            {
               return;
            }
            else
            {
               throw ex;
            }
         }

         string reportPath = Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments);
         string reportFile = reportPath + @"\BalanceDue.pdf";

         Stream reportStream = response.Content.ReadAsStreamAsync().Result;
         if (reportStream.GetType().Name == "MemoryStream")
         {
            if (File.Exists(reportFile))
            {
               File.Delete(reportFile);
            }

            Stream fileStream = File.Create(reportFile);
            reportStream.CopyTo(fileStream);

            fileStream.Close();
            reportStream.Close();
         }

         if (File.Exists(reportFile))
         {
            Process.Start(reportFile);
         }
      }

      static public async Task GetOccupancyListing(List<int> propertyIDs, List<int> unitIDs, DateTime asOfDate)
      {
         string pIDs = string.Join(",", propertyIDs);
         string uIDs = string.Join(",", unitIDs);
         string date = $"{asOfDate.Year}/{asOfDate.Month}/{asOfDate.Day}";
         HttpResponseMessage response = await HttpClientHelper.Client.GetAsync($"/Reports/14/RunReport?parameters=PropertyIDs,({pIDs});UNITIDS,({uIDs});AsOfDate,{date}&GetOptions=ReturnPDFUrl");
         try
         {
            response.EnsureSuccessStatusCode();
         }
         catch (HttpRequestException ex)
         {
            if (response.StatusCode == System.Net.HttpStatusCode.NotFound)
            {
               return;
            }
            else
            {
               throw ex;
            }
         }

         JValue item = response.Content.ReadAsAsync<JValue>().Result;
         Uri reportUri = new Uri((string)item.Value);

         string reportPath = Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments);
         string reportFile = reportPath + @"\OccupancyListing.pdf";

         if (File.Exists(reportFile))
         {
            File.Delete(reportFile);
         }

         using (WebClient client = new WebClient())
         {
            client.DownloadFile(reportUri, reportFile);
         }

         if (File.Exists(reportFile))
         {
            Process.Start(reportFile);
         }
      }
   }
}