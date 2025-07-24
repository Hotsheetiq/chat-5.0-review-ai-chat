using System;
using System.Collections.Generic;

namespace LCS.UI.API.QuickStart.Examples.Models
{
   public class PropertyModel
   {
      public int PropertyID { get; set; }
      public string Name { get; set; }
      public string ShortName { get; set; }
      public string BillingName1 { get; set; }
      public string BillingName2 { get; set; }
      public string ManagerName { get; set; }
      public bool IsActive { get; set; }
      public bool IsCommercial { get; set; }
      public string Email { get; set; }
      public string TaxID { get; set; }
      public string Comment { get; set; }
      public int ImageID { get; set; }
      public int ServiceManagerAssignedUserID { get; set; }
      public bool IsAllocationOrderDisabled { get; set; }
      public bool IsAllocationOrderSortedByMonth { get; set; }
      public bool IsOverwriteTimeZone { get; set; }
      public bool IsDaylightSavingsTime { get; set; }
      public DateTime CreateDate { get; set; }
      public DateTime UpdateDate { get; set; }
      public int CreateUserID { get; set; }
      public int UpdateUserID { get; set; }
      public bool IsLateChargeEnabled { get; set; }
      public bool IsEpayEnabled { get; set; }
      public bool IsEndorsementOverride { get; set; }
      public string EndorsementOverride { get; set; }
      public int SquareFootage { get; set; }
      public int DefaultBankID { get; set; }
      public int PrimaryOwnerID { get; set; }
      public int PostingDay { get; set; }
      public int CheckTemplateID { get; set; }
      public DateTime LastMonthlyPost { get; set; }
      public DateTime LastWeeklyPost { get; set; }
      public DateTime LastDailyPost { get; set; }
      public DateTime LastManagementFeePost { get; set; }
      public List<PhoneNumberModel> PhoneNumbers { get; set; }
      public List<AddressModel> Addresses { get; set; }
      public AddressModel PrimaryAddress { get; set; }
      public AddressModel BillingAddress { get; set; }
      public List<SelectListItemModel> RentChargeTypes { get; set; }
      public List<SelectListItemModel> PropertyFloors { get; set; }
      public List<SelectListItemModel> PropertyBanks { get; set; }
   }
}