using System;

namespace LCS.UI.API.QuickStart.Examples.Models
{
   public class ContactModel
   {
      public string APIURI { get; set; }
      public int ContactID { get; set; }
      public string FirstName { get; set; }
      public string MiddleName { get; set; }
      public string LastName { get; set; }
      public bool IsPrimary { get; set; }
      public int ContactTypeID { get; set; }
      public DateTime DateOfBirth { get; set; }
      public string FederalTaxID { get; set; }
      public string Comment { get; set; }
      public string Email { get; set; }
      public string License { get; set; }
      public string Car { get; set; }
      public int PictureID { get; set; }
      public bool IsShowOnBill { get; set; }
      public string Employer { get; set; }
      public string ApplicantType { get; set; }
      public DateTime CreateDate { get; set; }
      public int CreateUserID { get; set; }
      public DateTime UpdateDate { get; set; }
      public int UpdateUserID { get; set; }
   }
}
