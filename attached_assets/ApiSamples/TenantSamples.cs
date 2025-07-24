using LCS.UI.API.QuickStart.Examples.Helpers;
using LCS.UI.API.QuickStart.Examples.Models;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace LCS.UI.API.QuickStart.Examples.ApiSamples
{
   public class TenantSamples
   {
      //------------------------------------------------------------------------------------------------------
      // Tenant Collection Apis
      //------------------------------------------------------------------------------------------------------

      static public async Task GetAll()
      {
         List<TenantModel> tenants = await HttpClientHelper.GetCollectionReturningModels<TenantModel>("/tenants");
      }

      static public async Task GetAllWithEmbeddedContacts()
      {
         List<TenantModel> tenants = await HttpClientHelper.GetCollectionReturningModels<TenantModel>("/tenants?embeds=Contacts");
      }

      static public async Task GetFilteredByPropertyID(int propertyID)
      {
         List<TenantModel> tenants = await HttpClientHelper.GetCollectionReturningModels<TenantModel>($"/tenants?filters=PropertyID,eq,{propertyID}");
      }

      static public async Task GetFilteredByPropertyIDAndNameStartsWith(int propertyID, string nameStartsWith)
      {
         List<TenantModel> tenants = await HttpClientHelper.GetCollectionReturningModels<TenantModel>($"/tenants?filters=PropertyID,eq,{propertyID};Name,sw,{nameStartsWith}");
      }

      static public async Task GetFilteredByPropertyIDAndNameStartsWithOrderedByName(int propertyID, string nameStartsWith)
      {
         List<TenantModel> tenants = await HttpClientHelper.GetCollectionReturningModels<TenantModel>($"/tenants?filters=PropertyID,eq,{propertyID};Name,sw,{nameStartsWith}&orderingOptions=TenantName");
      }

      static public async Task GetSelectedFields()
      {
         List<TenantModel> tenants = await HttpClientHelper.GetCollectionReturningModels<TenantModel>("/tenants?fields=ActiveStartDate,Name");
      }

      //------------------------------------------------------------------------------------------------------
      // Single Tenant Apis
      //------------------------------------------------------------------------------------------------------

      static public async Task Get(int tenantID)
      {
         TenantModel tenant = await HttpClientHelper.GetSingleReturningModel<TenantModel>($"/tenants/{tenantID}");
      }

      static public async Task GetWithEmbeddedAddressesAndContacts(int tenantID)
      {
         TenantModel tenant = await HttpClientHelper.GetSingleReturningModel<TenantModel>($"/tenants/{tenantID}?embeds=Addresses,Contacts");
      }

      static public async Task GetWithEmbeds(int tenantID)
      {
         TenantModel tenant = await HttpClientHelper.GetSingleReturningModel<TenantModel>($"/tenants/{tenantID}?embeds=Addresses,Color,Contacts,PrimaryContact,PrimaryContactPhoneNumbers,Property");
      }

      static public async Task SaveExistingUsingCustomModelAndIncludedFields(int tenantID)
      {
         TenantModel tenant = await HttpClientHelper.GetSingleReturningModel<TenantModel>($"/tenants/{tenantID}");

         if (tenant != null)
         {
            var tenantToUpdate = new TenantUpdateModel();
            tenantToUpdate.TenantID = tenant.TenantID;
            tenantToUpdate.FirstName = "Edie";
            tenantToUpdate.LastName = tenant.LastName;
            tenantToUpdate.Comment = "Sample Comment";
            tenantToUpdate.UpdateDate = tenant.UpdateDate;
            tenantToUpdate.UpdateUserID = tenant.UpdateUserID;

            TenantUpdateModel tenantUpdate = await HttpClientHelper.PostSingle<TenantUpdateModel>("/tenants?fields=TenantID,FirstName,LastName,Comment,UpdateDate,UpdateUserID", tenantToUpdate);
         }
      }

      //------------------------------------------------------------------------------------------------------
      // Tenant Included Resource Apis
      //------------------------------------------------------------------------------------------------------

      static public async Task GetContacts(int tenantID)
      {
         List<ContactModel> contacts = await HttpClientHelper.GetCollectionReturningModels<ContactModel>($"/tenants/{tenantID}/Contacts");
      }

      static public async Task GetAddresses(int tenantID)
      {
         List<AddressModel> addresses = await HttpClientHelper.GetCollectionReturningModels<AddressModel>($"/tenants/{tenantID}/Addresses");
      }

      static public async Task GetPrimaryContact(int tenantID)
      {
         ContactModel contact = await HttpClientHelper.GetSingleReturningModel<ContactModel>($"/tenants/{tenantID}/PrimaryContact");
      }
   }
}
