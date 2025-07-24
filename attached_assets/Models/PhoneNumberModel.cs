namespace LCS.UI.API.QuickStart.Examples.Models
{
   public class PhoneNumberModel
   {
      public int PhoneNumberTypeID { get; set; }
      public int PhoneNumberID { get; set; }
      public string Name { get; set; }
      public string Description { get; set; }
      public int SortOrder { get; set; }
      public string PhoneNumber { get; set; }
      public string Extension { get; set; }
      public string StrippedPhoneNumber { get; set; }
      public bool IsPrimary { get; set; }
   }
}
