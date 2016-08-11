<?xml version="1.0"?>
<SMTK_AttributeSystem Version="2">
  <!--**********  Category and Analysis Information ***********-->
  <!--**********  Attribute Definitions ***********-->
  <Definitions>
    <AttDef Type="ResampleOptions" BaseType="" Version="0" Unique="true">
      <ItemDefinitions>
        <Int Name="period" Label="Period" NumberOfRequiredValues="1">
          <BriefDescription>Resample Frequency</BriefDescription>
            <DiscreteInfo DefaultIndex="daily">
              <Value Enum="Daily">daily</Value>
              <Value Enum="Weekly">weekly</Value>
              <Value Enum="Monthly">monthly</Value>
              <Value Enum="Annualy">annual</Value>
            </DiscreteInfo>
        </Int>
        <Int Name="method" Label="Method" NumberOfRequiredValues="1">
          <BriefDescription>Resample Frequency</BriefDescription>
            <DiscreteInfo DefaultIndex="mean">
              <Value Enum="Sum">sum</Value>
              <Value Enum="Mean">mean</Value>
              <Value Enum="Std">std</Value>
              <Value Enum="Max">max</Value>
              <Value Enum="Min">min</Value>
              <Value Enum="Median">median</Value>
            </DiscreteInfo>
        </Int>
      </ItemDefinitions>
    </AttDef>
  </Definitions>
  <!--********** Workflow Views ***********-->
  <Views>
    <View Type="Instanced" Title="Options">
      <InstancedAttributes>
        <Att Name="Options" Type="ResampleOptions" />
      </InstancedAttributes>
    </View>
  </Views>
</SMTK_AttributeSystem>
