namespace LCS.UI.API.QuickStart.Examples.Models
{
   public class AddressModel
   {
      public int AddressID { get; set; }
      public int AddressTypeID { get; set; }
      public string Address { get; set; }
      public string Street1 { get; set; }
      public string Street2 { get; set; }
      public string City { get; set; }
      public string State { get; set; }
      public string PostalCode { get; set; }
      public int CountryID { get; set; }
      public bool IsPrimary { get; set; }
      public bool IsBilling { get; set; }
      public string Name { get; set; }
      public string Description { get; set; }
      public int SortOrder { get; set; }
   }
}