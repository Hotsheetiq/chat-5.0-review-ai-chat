using System;
using System.Collections.Generic;

namespace LCS.UI.API.QuickStart.Examples.Models
{
   public class TenantModel
   {
      public int TenantID { get; set; }
      public string Name { get; set; }
      public string FirstName { get; set; }
      public string LastName { get; set; }
      public bool IsCompany { get; set; }
      public int ColorID { get; set; }
      public string Comment { get; set; }
      public int RentDueDay { get; set; }
      public string LeasePeriod { get; set; }
      public bool DoNotChargeLateFees { get; set; }
      public bool DoNotPrintStatements { get; set; }
      public bool DoNotAcceptChecks { get; set; }
      public bool IsProspect { get; set; }
      public int LeasingAgentID { get; set; }
      public int AccountGroupID { get; set; }
      public int TotalCalls { get; set; }
      public int FailedCalls { get; set; }
      public int DisplayID { get; set; }
      public bool IsAccountGroupMaster { get; set; }
      public int TotalVisits { get; set; }
      public int TotalEmails { get; set; }
      public DateTime FirstContact { get; set; }
      public DateTime LastContact { get; set; }
      public int PropertyID { get; set; }
      public DateTime ActiveStartDate { get; set; }
      public DateTime ActiveEndDate { get; set; }
      public bool DoNotAcceptPayments { get; set; }
      public int DefaultTaxTypeID { get; set; }
      public DateTime CreateDate { get; set; }
      public int CreateUserID { get; set; }
      public DateTime UpdateDate { get; set; }
      public int UpdateUserID { get; set; }
      public List<ContactModel> Contacts { get; set; }
      public ColorModel Color { get; set; }
      public PropertyModel Property { get; set; }
      public List<PhoneNumberModel> PrimaryContactPhoneNumbers { get; set; }
      public List<LeaseModel> Leases { get; set; }
      public List<AddressModel> Addresses { get; set; }
   }
}
