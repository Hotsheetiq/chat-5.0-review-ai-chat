using System.Collections.Generic;

namespace LCS.UI.API.QuickStart.Examples.Models
{
   public class ColorModel
   {
      public int ColorID { get; set; }
      public string Name { get; set; }
      public bool IsDisplayColor { get; set; }
      public string HexValue { get; set; }
      public List<EntityTypeModel> EntityTypes { get; set; }
   }
}