//----------------------------------------------------------------------------------------------------------------------
//   Rent Manager 12 Web API Samples
//   
//   Copyright © 2015 by London Computer Systems, Inc.
//   
//   Version 1.0. All rights reserved. This guide, as well as the software described in it, is furnished under 
//   license and may only be used or copied in accordance with the terms of such license.
//
//   Except as permitted by such license, no part of the contents of this guide may be reproduced or transmitted 
//   in any form or by any means without the written permission of the author.
//
//   These samples are furnished for informational use only, is subject to change without notice, and should 
//   not be construed as a commitment by London Computer Systems, Inc.
//
//   London Computer Systems, Inc. assumes no responsibility or liability for any errors or inaccuracies that may 
//   appear in this guide.  Data used in examples herein is fictitious unless otherwise noted. Any similarity with 
//   actual working data is coincidental.
//
//   Notes:
//   1) The IDs used throughout these samples may or may not correspond to identifiers used in your RMO database.
//      Please adjust accordingly.
//
//----------------------------------------------------------------------------------------------------------------------

using LCS.UI.API.QuickStart.Examples.ApiSamples;
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace LCS.UI.API.QuickStart.Examples
{
   class Program
   {
      static void Main()
      {
         Console.WriteLine("Starting Rent Manager API Samples...");
         try
         {
            RunAsync().Wait();
            Console.WriteLine("Completion of Rent Manager API Samples...");
         }
         catch (Exception ex)
         {
            Console.WriteLine("Rent Manager API Samples failed with the following error:");
            Console.WriteLine("..." + ex.Message);
            Console.WriteLine("..." + ex.InnerException.Message);
         }
         finally
         {
            Console.WriteLine("Press enter to close...");
            Console.ReadLine();
         }
      }

      static async Task RunAsync()
      {
         //------------------------------------------------------------------------------------------------------
         // Authorize the user
         //------------------------------------------------------------------------------------------------------

         AuthorizationSamples.Authorize().Wait();

         //------------------------------------------------------------------------------------------------------
         // Color API Samples
         //------------------------------------------------------------------------------------------------------
         #region Colors
         Console.WriteLine("Running color API samples...");

         // Get all colors
         await ColorSamples.GetAllReturningModels();
         await ColorSamples.GetAllReturningJson();

         // Get one color
         await ColorSamples.GetReturningModel();
         await ColorSamples.GetReturningJson();

         // Update one color
         await ColorSamples.Update();

         // Update several colors
         await ColorSamples.UpdateCollection();
         #endregion

         //------------------------------------------------------------------------------------------------------
         // Tenant API Samples
         //------------------------------------------------------------------------------------------------------
         #region Tenants
         Console.WriteLine("Running tenant API samples...");

         // Get all tenants
         await TenantSamples.GetAll();

         // Get all tenants with embedded contacts
         await TenantSamples.GetAllWithEmbeddedContacts();

         // Update variables for propertyID, tenantID, and name to match your data
         int propertyID = 1;
         int tenantID = 1;
         string nameStartsWith = "A";

         #region Returns 204: No Content if it does not exist, will not throw exception
         // Get filtered tenants
         await TenantSamples.GetFilteredByPropertyID(propertyID);

         // Get filtered tenants
         await TenantSamples.GetFilteredByPropertyIDAndNameStartsWith(propertyID, nameStartsWith);

         // Get all tenants with selected fields
         await TenantSamples.GetFilteredByPropertyIDAndNameStartsWithOrderedByName(propertyID, nameStartsWith);
         #endregion

         #region Returns 404: Not Found if it does not exist, will not throw exception
         // Get one tenant
         await TenantSamples.Get(tenantID);

         // Get one tenant with embedded addresses and contacts
         await TenantSamples.GetWithEmbeddedAddressesAndContacts(tenantID);

         // Get one tenant with embeds
         await TenantSamples.GetWithEmbeds(tenantID);

         // Save existing tenant using a custom model and returning selected fields
         // !!!!!! This will update existing data to new values !!!!!
         await TenantSamples.SaveExistingUsingCustomModelAndIncludedFields(tenantID);
         #endregion

         #region Returns 500: Internal Server Error if it does not exist, will throw exceptions
         // Get all contacts for a tenant
         await TenantSamples.GetContacts(tenantID);

         // Get all addresses for a tenant
         await TenantSamples.GetAddresses(tenantID);

         // Get primary contact for a tenant
         await TenantSamples.GetPrimaryContact(tenantID);
         #endregion
         #endregion

         //------------------------------------------------------------------------------------------------------
         // Report API Samples
         //------------------------------------------------------------------------------------------------------
         #region Reports
         Console.WriteLine("Running report API samples...");

         await ReportSamples.GetBalanceDueReportAsPdfAndSaveToDisk(propertyID);

         await ReportSamples.GetBalanceDueReportAsPdfAndSaveToDiskAndLaunchInViewer(propertyID);

         List<int> propertyIDs = new List<int> { 1, 2, 3 };
         List<int> unitIDs = new List<int> { 311, 312, 313 };
         DateTime asOfDate = DateTime.Now;

         await ReportSamples.GetOccupancyListing(propertyIDs, unitIDs, asOfDate);
         #endregion
      }
   }
}
